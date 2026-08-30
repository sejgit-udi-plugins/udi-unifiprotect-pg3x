"""UniFi Protect controller node."""

import asyncio
import os
import threading
import time

import aiohttp
import udi_interface

from nodes.Camera import Camera
from utils.async_bridge import AsyncBridge
from utils.profile import write_profile
from utils.protect_client import ProtectClient

LOGGER = udi_interface.LOGGER

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROFILE_DIR = os.path.join(_PLUGIN_DIR, 'profile')

_WATCHDOG_DEFAULT_MIN = 5
_RESTART_COOLDOWN_SEC = 1800
_NOTICE_AFTER_SEC = 60


class Controller(udi_interface.Node):
    id = 'unifi_controller'

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
    ]

    def __init__(self, polyglot, primary, address, name):
        super().__init__(polyglot, primary, address, name)

        self._async = AsyncBridge()
        self._client = None
        self._cameras = {}
        self.ringtones = []
        self.detection_timeout = 300
        self._initialized = False
        self._controller_added = False
        self._node_events = {}
        self._node_events_lock = threading.Lock()
        self._params = udi_interface.Custom(polyglot, 'customparams')
        self._data = udi_interface.Custom(polyglot, 'customdata')
        self._down_since = None
        self._watchdog_minutes = _WATCHDOG_DEFAULT_MIN
        self._running = True
        self._connect_lock = threading.Lock()
        self._profile_written = False

        polyglot.subscribe(polyglot.CONFIGDONE, self._on_config_done)
        polyglot.subscribe(polyglot.START, self.start, address)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.param_handler)
        polyglot.subscribe(polyglot.CUSTOMDATA, self._customdata_handler)
        polyglot.subscribe(polyglot.POLL, self.poll)
        polyglot.subscribe(polyglot.STOP, self.stop)
        polyglot.subscribe(polyglot.ADDNODEDONE, self._on_node_added)

        polyglot.ready()
        polyglot.addNode(self)

    def start(self):
        LOGGER.info(
            'Started UniFi Protect NodeServer %s',
            self.poly.serverdata.get('version', ''),
        )
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()

    def _customdata_handler(self, data):
        self._data.load(data or {})

    def stop(self):
        LOGGER.info('Stopping UniFi Protect nodeserver')
        self._running = False
        if self._client:
            self._async.run(self._client.close(), timeout=10)
        self._async.shutdown()

    def _on_config_done(self):
        if self._controller_added:
            return
        LOGGER.info('Config done — adding controller node')
        try:
            self._add_node_wait(self, timeout=3)
            self._controller_added = True
            self.setDriver('ST', 0)
            if not self._initialized:
                self._try_connect()
        except Exception as e:
            LOGGER.error(f'Failed to add controller node: {e}', exc_info=True)

    def _on_node_added(self, data):
        addr = (data or {}).get('address')
        with self._node_events_lock:
            if addr is None:
                waiters = list(self._node_events.values())
            else:
                ev = self._node_events.get(addr)
                waiters = [ev] if ev else []
        for e in waiters:
            e.set()

    def _add_node_wait(self, node, timeout=15):
        ev = threading.Event()
        with self._node_events_lock:
            self._node_events[node.address] = ev
        try:
            self.poly.addNode(node)
            if not ev.wait(timeout=timeout):
                LOGGER.warning(f'Timed out waiting for ISY to add {node.address}')
        finally:
            with self._node_events_lock:
                self._node_events.pop(node.address, None)

    def param_handler(self, params):
        if params:
            self._params.load(params)
        else:
            LOGGER.warning("CUSTOMPARAMS with no data — applying defaults")

        defaults = {
            "host": "unifi.local",
            "port": "443",
            "api_key": "",
            "username": "admin",
            "password": "",
            "verify_ssl": "false",
            "detection_timeout": "300",
            "watchdog_minutes": "5",
        }
        for param, default_value in defaults.items():
            if param not in self._params:
                self._params[param] = default_value
            elif default_value and not str(self._params.get(param, "")).strip():
                self._params[param] = default_value

        self.poly.Notices.delete("config")

        try:
            self.detection_timeout = max(
                0, int((self._params.get("detection_timeout") or "300").strip()))
        except (ValueError, TypeError):
            self.detection_timeout = 300

        host = (self._params.get("host") or "").strip()
        api_key = (self._params.get("api_key") or "").strip()
        username = (self._params.get("username") or "").strip()
        password = (self._params.get("password") or "").strip()

        if not host:
            self.poly.Notices["config"] = "Set host in Custom Parameters"
            return
        if not username or not password:
            self.poly.Notices["config"] = (
                "username and password required (Protect bootstrap/WebSocket "
                "need session auth; api_key alone is not supported)")
            return

        if not self._initialized:
            self._try_connect()

    def _is_configured(self) -> bool:
        p = self._params
        host = (p.get('host') or '').strip()
        user = (p.get('username') or '').strip()
        passwd = (p.get('password') or '').strip()
        if host and user and passwd:
            return True
        try:
            cfg = (self.poly.getConfig() or {}).get('customParams') or {}
        except Exception:
            return False
        if not (cfg.get('host') or '').strip():
            return False
        if (cfg.get('username') or '').strip() and (cfg.get('password') or '').strip():
            LOGGER.warning('Recovered params from PG3 config')
            self._params.load(cfg)
            return True
        return False

    def _try_connect(self):
        with self._connect_lock:
            if self._initialized:
                return
            self._initialized = True

        params = self._params
        host = (params.get('host') or '').strip()
        api_key = (params.get('api_key') or '').strip()
        user = (params.get('username') or '').strip()
        passwd = (params.get('password') or '').strip()
        port = int((params.get('port') or '443').strip())
        verify = (params.get('verify_ssl') or 'false').strip().lower() == 'true'
        try:
            self._watchdog_minutes = int(
                (params.get('watchdog_minutes') or _WATCHDOG_DEFAULT_MIN))
        except (ValueError, TypeError):
            self._watchdog_minutes = _WATCHDOG_DEFAULT_MIN

        if not host or not user or not passwd:
            LOGGER.warning('Incomplete auth params — not connecting')
            self._initialized = False
            return

        self._async.submit(
            self._supervisor(host, port, api_key, user, passwd, verify))

    async def _supervisor(self, host, port, api_key, username, password, verify_ssl):
        try:
            await self._supervise(host, port, api_key, username, password, verify_ssl)
        finally:
            LOGGER.info('Connection supervisor stopped')
            self._initialized = False

    async def _supervise(self, host, port, api_key, username, password, verify_ssl):
        backoff = 5
        first = True
        while self._running:
            try:
                LOGGER.info(f'Connecting to UniFi Protect at {host}:{port}')
                self._client = ProtectClient(
                    host, port,
                    api_key=api_key,
                    username=username,
                    password=password,
                    verify_ssl=verify_ssl)
                await self._client.connect()

                bootstrap = await self._client.get_bootstrap()
                LOGGER.info('Bootstrap received')

                if not self._profile_written:
                    try:
                        self.ringtones = await self._client.get_ringtones()
                        LOGGER.info(f'Ringtones: {[r["name"] for r in self.ringtones]}')
                    except Exception as e:
                        LOGGER.warning(f'Could not fetch ringtones: {e}')
                        self.ringtones = []
                    write_profile(_PROFILE_DIR, self.ringtones)
                    self.poly.updateProfile()
                    self._profile_written = True

                if first:
                    await asyncio.sleep(2)
                    first = False

                LOGGER.info('Discovering cameras')
                await asyncio.get_event_loop().run_in_executor(
                    None, self._discover_cameras, bootstrap)

                LOGGER.info('Listening for WebSocket events')
                backoff = 5
                await self._client.listen(self._on_ws_message,
                                          on_connect=self._mark_online)
                LOGGER.warning('WebSocket closed by peer')
                self._mark_offline('WebSocket closed')
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._mark_offline(e)

            await self._teardown_client()
            if not self._running:
                break
            LOGGER.info(f'Retrying in {backoff}s')
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    async def _teardown_client(self):
        self.setDriver('ST', 0)
        client, self._client = self._client, None
        if client:
            try:
                await client.close()
            except Exception as e:
                LOGGER.debug(f'Error closing client: {e}')

    def _mark_online(self):
        self.setDriver('ST', 1)
        if self._down_since is not None:
            down_min = (time.time() - self._down_since) / 60
            LOGGER.info(f'Connection restored after {down_min:.1f} min offline')
            self._down_since = None
        self.poly.Notices.delete('offline')

    def _mark_offline(self, err):
        now = time.time()
        if self._down_since is None:
            self._down_since = now
        down_sec = now - self._down_since
        LOGGER.warning(f'Connection failed (down {down_sec / 60:.1f} min): {err}')

        if down_sec >= _NOTICE_AFTER_SEC:
            self.poly.Notices['offline'] = (
                f'No connection to UniFi Protect for {down_sec / 60:.0f} min: {err}')

        if not self._watchdog_minutes or down_sec < self._watchdog_minutes * 60:
            return

        last = float(self._data.get('last_restart') or 0)
        if now - last < _RESTART_COOLDOWN_SEC:
            return
        self._data['last_restart'] = now
        LOGGER.error(f'No connection for {down_sec / 60:.0f} min — restarting plugin')
        try:
            self.poly.restart()
        except Exception as e:
            LOGGER.error(f'Self-restart failed: {e}')

    def _discover_cameras(self, bootstrap: dict):
        cameras = bootstrap.get('cameras') or []
        if isinstance(cameras, dict):
            cameras = cameras.values()
        for cam in cameras:
            self._ensure_camera(cam)

    def _ensure_camera(self, cam: dict):
        cam_id = cam.get('id', '')
        mac = cam.get('mac', '')
        address = mac.lower().replace(':', '')[:14] if mac else cam_id[:14].lower().replace('-', '')
        if address in self._cameras:
            return self._cameras[address]

        name = cam.get('name') or cam_id
        node = Camera(self.poly, self.address, address, name, cam_id, self)
        self._add_node_wait(node, timeout=3)
        node.clear_detections()
        node.set_connected(cam.get('state', '') == 'CONNECTED')
        if cam.get('speakerSettings'):
            node.set_speaker(cam['speakerSettings'])
        self._cameras[address] = node
        LOGGER.info(f'Added camera: {name} ({address})')
        return node

    def _node_for_camera(self, camera_id: str):
        for node in self._cameras.values():
            if node.camera_id == camera_id:
                return node
        return None

    def _on_ws_message(self, action: dict, data: dict):
        try:
            model_key = action.get('modelKey', '')
            act = action.get('action', '')

            if model_key == 'camera':
                cam_id = action.get('id', '')
                node = self._node_for_camera(cam_id)
                if node and 'state' in data:
                    node.set_connected(data['state'] == 'CONNECTED')
                elif not node and act == 'add':
                    LOGGER.info(f'New camera detected ({cam_id}) — resyncing')
                    self._async.submit(self._resync())

            elif model_key == 'event':
                self._handle_event(action, data)

        except Exception as e:
            LOGGER.error(f'Error handling WS message: {e}', exc_info=True)

    def _handle_event(self, action: dict, data: dict):
        cam_id = data.get('camera') or data.get('cameraId')
        if not cam_id:
            return

        node = self._node_for_camera(cam_id)
        if not node:
            return

        evt_type = data.get('type', '')
        is_open = data.get('end') is None

        if evt_type == 'motion':
            node.set_motion(is_open)
        elif evt_type == 'smartDetectZone':
            for obj in (data.get('smartDetectTypes') or []):
                node.set_smart(obj, is_open)

    def poll(self, flag):
        if flag == 'shortPoll':
            if not self._initialized and self._is_configured():
                LOGGER.warning('No connection supervisor running — starting one')
                self._try_connect()
            return
        if flag == 'longPoll' and self._initialized and self._client:
            self._async.submit(self._resync())

    async def _resync(self):
        try:
            bootstrap = await self._client.get_bootstrap()
        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                try:
                    LOGGER.info('Resync 401 — creating fresh session')
                    await self._client.reconnect()
                    bootstrap = await self._client.get_bootstrap()
                except Exception as e2:
                    LOGGER.warning(f'Resync failed after reconnect: {e2}')
                    return
            else:
                LOGGER.warning(f'Resync failed: {e}')
                return
        except Exception as e:
            LOGGER.warning(f'Resync failed: {e}')
            return
        cameras = bootstrap.get('cameras') or []
        if isinstance(cameras, dict):
            cameras = cameras.values()
        for cam in cameras:
            node = self._node_for_camera(cam.get('id', ''))
            if node:
                node.set_connected(cam.get('state', '') == 'CONNECTED')
                if cam.get('speakerSettings'):
                    node.set_speaker(cam['speakerSettings'])

    def query(self, command=None):
        self.reportDrivers()
        for node in self._cameras.values():
            node.query()

    def cmd_discover(self, command=None):
        if not self._initialized:
            self._try_connect()
        elif self._client:
            self._async.submit(self._resync())

    commands = {
        'QUERY': query,
        'DISCOVER': cmd_discover,
    }
