"""Run asyncio coroutines from Polyglot's synchronous node threads."""

import asyncio
import threading

import udi_interface

LOGGER = udi_interface.LOGGER


class AsyncBridge:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name='unifi-async')
        self._thread.start()

    def run(self, coro, timeout=30):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            LOGGER.error('Async call timed out')
            return None
        except Exception as e:
            LOGGER.error(f'Async error: {e}')
            return None

    def submit(self, coro):
        def _log_exception(fut):
            if not fut.cancelled() and fut.exception():
                LOGGER.error(f'Async task error: {fut.exception()}')

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        future.add_done_callback(_log_exception)

    def shutdown(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
