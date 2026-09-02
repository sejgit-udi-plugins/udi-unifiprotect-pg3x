"""UniFi Protect controller node."""

import asyncio
import threading
import time

import aiohttp
import udi_interface

from nodes.Camera import Camera
from nodes.Sensor import Sensor
from utils import sensor_state
from utils.async_bridge import AsyncBridge
from utils.camera_caps import camera_nodedef_for
from utils.protect_client import ProtectClient, device_address
from utils.sensor_caps import capability_config_changed, sensor_capabilities
from utils.sensor_nodedef import sensor_nodedef_for_caps
from utils.temperature import normalize_units

LOGGER = udi_interface.LOGGER

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
        self._sensors = {}
        self.detection_timeout = 300
        self.temperature_units = 'F'
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
            "verify_ssl": "false",
            "detection_timeout": "300",
            "watchdog_minutes": "5",
            "temperature_units": "F",
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

        self.temperature_units = normalize_units(
            self._params.get("temperature_units") or "F")

        host = (self._params.get("host") or "").strip()
        api_key = (self._params.get("api_key") or "").strip()

        if not host:
            self.poly.Notices["config"] = "Set host in Custom Parameters"
            return
        if not api_key:
            self.poly.Notices["config"] = "Set api_key in Custom Parameters"
            return

        if not self._initialized:
            self._try_connect()

    def _is_configured(self) -> bool:
        p = self._params
        if (p.get('host') or '').strip() and (p.get('api_key') or '').strip():
            return True
        try:
            cfg = (self.poly.getConfig() or {}).get('customParams') or {}
        except Exception:
            return False
        if (cfg.get('host') or '').strip() and (cfg.get('api_key') or '').strip():
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
        port = int((params.get('port') or '443').strip())
        verify = (params.get('verify_ssl') or 'false').strip().lower() == 'true'
        try:
            self._watchdog_minutes = int(
                (params.get('watchdog_minutes') or _WATCHDOG_DEFAULT_MIN))
        except (ValueError, TypeError):
            self._watchdog_minutes = _WATCHDOG_DEFAULT_MIN

        if not host or not api_key:
            LOGGER.warning('Incomplete auth params — not connecting')
            self._initialized = False
            return

        self._async.submit(self._supervisor(host, port, api_key, verify))

    async def _supervisor(self, host, port, api_key, verify_ssl):
        try:
            await self._supervise(host, port, api_key, verify_ssl)
        finally:
            LOGGER.info('Connection supervisor stopped')
            self._initialized = False

    async def _supervise(self, host, port, api_key, verify_ssl):
        backoff = 5
        while self._running:
            try:
                LOGGER.info(f'Connecting to UniFi Protect at {host}:{port}')
                self._client = ProtectClient(
                    host, port, api_key=api_key, verify_ssl=verify_ssl)
                await self._client.connect()

                cameras = await self._client.get_cameras()
                sensors = await self._client.get_sensors()
                LOGGER.info(
                    f'Loaded {len(cameras)} camera(s) and {len(sensors)} sensor(s) '
                    'from integration API')

                await asyncio.get_event_loop().run_in_executor(
                    None, self._discover_devices, cameras, sensors)

                LOGGER.info('Listening on integration event/device WebSockets')
                backoff = 5
                await self._client.listen(
                    self._on_integration_event,
                    self._on_integration_device,
                    on_connect=self._mark_online)
                LOGGER.warning('WebSocket subscriptions ended')
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

    def _discover_devices(self, cameras: list, sensors: list):
        for cam in cameras:
            self._ensure_camera(cam)
        for sensor in sensors:
            self._ensure_sensor(sensor)

    def _discover_cameras(self, cameras: list):
        for cam in cameras:
            self._ensure_camera(cam)

    def _ensure_camera(self, cam: dict):
        if (cam.get('modelKey') or 'camera') != 'camera':
            return
        cam_id = cam.get('id', '')
        address = device_address(cam)
        if not address:
            return
        nodedef_id = camera_nodedef_for(cam)
        if address in self._cameras:
            node = self._cameras[address]
            node.update_camera(cam)
            node.set_connected(cam.get('state', '') == 'CONNECTED')
            return node

        name = cam.get('name') or cam_id
        node = Camera(
            self.poly, self.address, address, name, cam_id, self,
            nodedef_id, cam)
        self._add_node_wait(node, timeout=3)
        node.clear_detections()
        node.set_connected(cam.get('state', '') == 'CONNECTED')
        self._cameras[address] = node
        LOGGER.info(f'Added camera: {name} ({address}) nodedef={nodedef_id}')
        return node

    def _ensure_sensor(self, sensor: dict):
        if (sensor.get('modelKey') or 'sensor') != 'sensor':
            return
        sensor_id = sensor.get('id', '')
        address = device_address(sensor)
        if not address:
            return
        caps = sensor_capabilities(sensor)
        nodedef_id = sensor_nodedef_for_caps(caps)
        if address in self._sensors:
            node = self._sensors[address]
            node.set_capabilities(caps)
            node.apply_state(sensor, replace=True)
            return node

        name = sensor.get('name') or sensor_id
        node = Sensor(
            self.poly, self.address, address, name, sensor_id, self,
            nodedef_id)
        node.set_capabilities(caps)
        self._add_node_wait(node, timeout=3)
        node.clear_detections()
        node.apply_state(sensor, replace=True)
        self._sensors[address] = node
        LOGGER.info(
            f'Added sensor: {name} ({address}) nodedef={nodedef_id} '
            f'caps={sorted(caps)}')
        return node

    def _node_for_sensor(self, sensor_id: str):
        for node in self._sensors.values():
            if node.sensor_id == sensor_id:
                return node
        return None

    def _node_for_camera(self, camera_id: str):
        for node in self._cameras.values():
            if node.camera_id == camera_id:
                return node
        return None

    def _on_integration_device(self, message: dict):
        try:
            item = message.get('item') or {}
            dev_id = item.get('id', '')
            model_key = item.get('modelKey', '')
            msg_type = message.get('type', '')

            if not model_key and dev_id:
                if self._node_for_sensor(dev_id):
                    model_key = 'sensor'
                elif self._node_for_camera(dev_id):
                    model_key = 'camera'

            if model_key == 'camera':
                node = self._node_for_camera(dev_id)
                if node and 'state' in item:
                    node.set_connected(item.get('state') == 'CONNECTED')
                elif msg_type == 'add' and not node:
                    LOGGER.info(f'New camera detected ({dev_id}) — resyncing')
                    self._async.submit(self._resync())
                return

            if model_key == 'sensor':
                node = self._node_for_sensor(dev_id)
                if node:
                    if capability_config_changed(item):
                        merged = sensor_state.merge_sensor_state(node._state, item)
                        node.set_capabilities(sensor_capabilities(merged))
                    node.apply_state(item)
                elif msg_type == 'add':
                    LOGGER.info(f'New sensor detected ({dev_id}) — resyncing')
                    self._async.submit(self._resync())
        except Exception as e:
            LOGGER.error(f'Error handling device message: {e}', exc_info=True)

    def _on_integration_event(self, message: dict):
        try:
            item = message.get('item') or {}
            if item.get('modelKey') != 'event':
                return
            self._handle_event(message.get('type', ''), item)
        except Exception as e:
            LOGGER.error(f'Error handling event message: {e}', exc_info=True)

    def _handle_event(self, change_type: str, data: dict):
        dev_id = data.get('device') or data.get('camera') or data.get('cameraId')
        if not dev_id:
            return

        cam_node = self._node_for_camera(dev_id)
        sensor_node = self._node_for_sensor(dev_id)
        if not cam_node and not sensor_node:
            return

        evt_type = (data.get('type') or '').strip()
        if change_type == 'remove':
            is_open = False
        else:
            is_open = data.get('end') is None

        smart_types = list(data.get('smartDetectTypes') or [])
        audio_types = list(data.get('smartDetectAudioTypes') or [])
        # Some API payloads list detections only in smartDetectEvents.
        extra_types = list(data.get('smartDetectEvents') or [])
        seen = set()
        bundled_types = []
        for obj in smart_types + audio_types + extra_types:
            key = str(obj)
            if key and key not in seen:
                seen.add(key)
                bundled_types.append(key)

        if cam_node:
            evt_lower = evt_type.lower()
            if evt_lower == 'motion':
                cam_node.set_motion(is_open)
            elif evt_lower == 'ring':
                cam_node.set_detection_type('ring', is_open)
            elif evt_lower == 'smartdetectline':
                LOGGER.info(
                    f'Line crossing event on {cam_node.name}: open={is_open}')
                cam_node.set_detection_type('line', is_open)
            elif evt_lower == 'smartaudiodetect' and not bundled_types:
                LOGGER.warning(
                    f'Audio detect event on {cam_node.name} with no types: '
                    f'{data.get("id", "")}')
            for obj in bundled_types:
                cam_node.set_detection_type(obj, is_open)

        if sensor_node:
            if evt_type == 'motion':
                sensor_node.set_motion(is_open)
            is_glass = any('glass' in str(t).lower() for t in bundled_types)
            if is_glass and sensor_state.CAP_GLASS in sensor_node._caps:
                sensor_node.set_glass_break(is_open)

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
            cameras = await self._client.get_cameras()
            sensors = await self._client.get_sensors()
        except aiohttp.ClientResponseError as e:
            LOGGER.warning(f'Resync failed: {e}')
            return
        except Exception as e:
            LOGGER.warning(f'Resync failed: {e}')
            return
        for cam in cameras:
            node = self._node_for_camera(cam.get('id', ''))
            if node:
                node.update_camera(cam)
                node.set_connected(cam.get('state', '') == 'CONNECTED')
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._ensure_camera, cam)
        for sensor in sensors:
            node = self._node_for_sensor(sensor.get('id', ''))
            if node:
                node.set_capabilities(sensor_capabilities(sensor))
                node.apply_state(sensor, replace=True)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._ensure_sensor, sensor)

    def query(self, command=None):
        self.reportDrivers()
        for node in self._cameras.values():
            node.query()
        for node in self._sensors.values():
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
