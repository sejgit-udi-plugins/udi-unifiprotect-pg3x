"""Minimal aiohttp-based UniFi Protect client with X-API-KEY support."""

import ssl

import aiohttp
import udi_interface

from .ws_protocol import parse_ws_message

LOGGER = udi_interface.LOGGER


class ProtectClient:
    """UniFi Protect API client.

    Authenticates with the official X-API-KEY header when ``api_key`` is set,
    otherwise falls back to local username/password cookie login.
    """

    def __init__(self, host: str, port: int, *,
                 api_key: str = '',
                 username: str = '',
                 password: str = '',
                 verify_ssl: bool = False):
        self.host = host
        self.port = port
        self.api_key = (api_key or '').strip()
        self.username = username
        self.password = password
        self._ssl = ssl.create_default_context() if verify_ssl else False
        self._session = None
        self._csrf_token = None
        self._auth_cookie = None
        self._last_update_id = None

    def _url(self, path: str) -> str:
        return f'https://{self.host}:{self.port}{path}'

    def _ws_url(self) -> str:
        base = f'wss://{self.host}:{self.port}/proxy/protect/ws/updates'
        if self._last_update_id:
            return f'{base}?lastUpdateId={self._last_update_id}'
        return base

    async def connect(self):
        self._session = aiohttp.ClientSession(
            cookie_jar=aiohttp.DummyCookieJar(),
            timeout=aiohttp.ClientTimeout(total=None, connect=10, sock_connect=10))
        if self.api_key:
            LOGGER.info('Using X-API-KEY authentication')
        else:
            await self._login()

    async def _login(self):
        resp = await self._session.post(
            self._url('/api/auth/login'),
            json={'username': self.username, 'password': self.password},
            ssl=self._ssl,
        )
        resp.raise_for_status()
        self._auth_cookie = None
        for header_val in resp.headers.getall('set-cookie', []):
            for part in header_val.split(';'):
                part = part.strip()
                if part.startswith('TOKEN='):
                    self._auth_cookie = part
                    break
            if self._auth_cookie:
                break
        self._csrf_token = (resp.headers.get('X-Csrf-Token')
                            or resp.headers.get('x-csrf-token')
                            or resp.headers.get('X-Updated-Csrf-Token'))
        LOGGER.info(f'Login: TOKEN={"found" if self._auth_cookie else "NOT FOUND"}, '
                    f'CSRF={"found" if self._csrf_token else "not found"}')

    def _headers(self) -> dict:
        h = {}
        if self.api_key:
            h['X-API-KEY'] = self.api_key
        if self._auth_cookie:
            h['Cookie'] = self._auth_cookie
        if self._csrf_token:
            h['X-Csrf-Token'] = self._csrf_token
        return h

    async def get_bootstrap(self) -> dict:
        resp = await self._session.get(
            self._url('/proxy/protect/api/bootstrap'),
            headers=self._headers(),
            ssl=self._ssl,
        )
        resp.raise_for_status()
        data = await resp.json()
        self._last_update_id = data.get('lastUpdateId')
        return data

    async def listen(self, on_message, on_connect=None):
        async with self._session.ws_connect(
                self._ws_url(), headers=self._headers(), ssl=self._ssl) as ws:
            if on_connect:
                on_connect()
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    action, data = parse_ws_message(msg.data)
                    if action and data:
                        uid = action.get('newUpdateId')
                        if uid:
                            self._last_update_id = uid
                        on_message(action, data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    LOGGER.warning(f'WebSocket closed/error: {msg.type}')
                    break

    async def get_ringtones(self) -> list:
        resp = await self._session.get(
            self._url('/proxy/protect/api/ringtones'),
            headers=self._headers(), ssl=self._ssl)
        resp.raise_for_status()
        return await resp.json()

    async def get_camera(self, camera_id: str) -> dict:
        resp = await self._session.get(
            self._url(f'/proxy/protect/api/cameras/{camera_id}'),
            headers=self._headers(), ssl=self._ssl)
        resp.raise_for_status()
        return await resp.json()

    async def patch_camera(self, camera_id: str, payload: dict):
        resp = await self._session.patch(
            self._url(f'/proxy/protect/api/cameras/{camera_id}'),
            headers=self._headers(), ssl=self._ssl, json=payload)
        if resp.status == 401:
            LOGGER.warning('patch_camera: 401 — reconnecting and retrying')
            await self.reconnect()
            resp = await self._session.patch(
                self._url(f'/proxy/protect/api/cameras/{camera_id}'),
                headers=self._headers(), ssl=self._ssl, json=payload)
        resp.raise_for_status()

    async def refresh_token(self):
        if self.api_key:
            return
        await self._login()
        LOGGER.info('Auth token refreshed')

    async def reconnect(self):
        await self.close()
        await self.connect()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
