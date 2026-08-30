"""UniFi Protect Public Integration API client (v1, X-API-KEY)."""

import asyncio
import json
import ssl
from typing import Any, Callable, Optional

import aiohttp
import udi_interface

LOGGER = udi_interface.LOGGER

_INTEGRATION_PREFIX = '/proxy/protect/integration/v1'


def unwrap_api_payload(payload: Any) -> Any:
    """Normalize v1 REST bodies (array or {"data": ...})."""
    if isinstance(payload, dict) and 'data' in payload:
        return payload['data']
    return payload


def camera_address(cam: dict) -> str:
    mac = (cam.get('mac') or '').strip()
    cam_id = (cam.get('id') or '').strip()
    if mac:
        return mac.lower().replace(':', '')[:14]
    return cam_id[:14].lower().replace('-', '')


class ProtectClient:
    """UniFi Protect Public Integration API client."""

    def __init__(self, host: str, port: int, *,
                 api_key: str,
                 verify_ssl: bool = False):
        self.host = host
        self.port = port
        self.api_key = (api_key or '').strip()
        self._ssl = ssl.create_default_context() if verify_ssl else False
        self._session: Optional[aiohttp.ClientSession] = None

    def _api_url(self, path: str) -> str:
        return f'https://{self.host}:{self.port}{_INTEGRATION_PREFIX}{path}'

    def _ws_url(self, path: str) -> str:
        return f'wss://{self.host}:{self.port}{_INTEGRATION_PREFIX}{path}'

    def _headers(self) -> dict:
        return {
            'X-API-KEY': self.api_key,
            'Accept': 'application/json',
        }

    async def connect(self):
        if not self.api_key:
            raise RuntimeError('api_key is required')
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, connect=10, sock_connect=10))
        LOGGER.info('Using UniFi Protect Public Integration API (X-API-KEY)')

    async def get_cameras(self) -> list:
        resp = await self._session.get(
            self._api_url('/cameras'),
            headers=self._headers(),
            ssl=self._ssl,
        )
        resp.raise_for_status()
        cameras = unwrap_api_payload(await resp.json())
        if not isinstance(cameras, list):
            raise RuntimeError(f'Unexpected cameras response: {type(cameras).__name__}')
        return cameras

    async def get_camera(self, camera_id: str) -> dict:
        resp = await self._session.get(
            self._api_url(f'/cameras/{camera_id}'),
            headers=self._headers(),
            ssl=self._ssl,
        )
        resp.raise_for_status()
        camera = unwrap_api_payload(await resp.json())
        if not isinstance(camera, dict):
            raise RuntimeError(f'Unexpected camera response: {type(camera).__name__}')
        return camera

    async def listen(self, on_event: Callable[[dict], None],
                     on_device: Callable[[dict], None],
                     on_connect: Optional[Callable[[], None]] = None):
        """Subscribe to official event and device WebSocket feeds."""
        connected = False

        def _mark_connected():
            nonlocal connected
            if not connected and on_connect:
                connected = True
                on_connect()

        await asyncio.gather(
            self._listen_ws('/subscribe/events', on_event, _mark_connected),
            self._listen_ws('/subscribe/devices', on_device, _mark_connected),
        )

    async def _listen_ws(self, path: str, callback: Callable[[dict], None],
                        on_first_message: Optional[Callable[[], None]]):
        first = True
        async with self._session.ws_connect(
                self._ws_url(path),
                headers=self._headers(),
                ssl=self._ssl,
                heartbeat=30) as ws:
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        LOGGER.warning(f'WebSocket {path} closed: {msg.type}')
                        break
                    continue
                if first:
                    first = False
                    if on_first_message:
                        on_first_message()
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError as exc:
                    LOGGER.debug(f'WebSocket {path} JSON error: {exc}')
                    continue
                if isinstance(payload, dict):
                    callback(payload)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
