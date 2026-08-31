"""UniFi Protect camera node."""

from __future__ import annotations

import threading
from copy import deepcopy

import udi_interface

from utils.binary_detect import set_binary_detection
from utils.camera_caps import camera_supports_smart_type
from utils.cmd_pairs import CONNECTED
from utils.camera_layouts import (
    CAMERA_DRIVERS,
    DETECTION_DRIVERS_BY_NODEDEF,
    cmd_pair_for_driver,
    lookup_detection,
)

LOGGER = udi_interface.LOGGER


class Camera(udi_interface.Node):
    id = 'unifi_camera_detect'

    drivers = CAMERA_DRIVERS['unifi_camera_detect']

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        camera_id,
        controller,
        nodedef_id: str,
        camera: dict | None = None,
    ):
        self.id = nodedef_id
        self.drivers = deepcopy(CAMERA_DRIVERS[nodedef_id])
        super().__init__(polyglot, primary, address, name)
        self.camera_id = camera_id
        self._ctrl = controller
        self._camera = camera or {}
        self._allowed = set(DETECTION_DRIVERS_BY_NODEDEF.get(nodedef_id, ()))
        self._timers = {}
        self._timer_lock = threading.Lock()

    def update_camera(self, camera: dict):
        self._camera = camera

    def _timeout_clear(self, driver: str):
        cmd_pair = self._cmd_pair_for_driver(driver)
        with self._timer_lock:
            self._timers.pop(driver, None)
        LOGGER.warning(
            f'{self.name}: {driver} auto-cleared after '
            f'{self._ctrl.detection_timeout}s (no close event received)')
        set_binary_detection(
            self,
            driver,
            False,
            cmd_pair=cmd_pair,
            timers=self._timers,
            timer_lock=self._timer_lock,
            timeout_sec=0,
            on_timeout=self._timeout_clear,
        )

    def _cmd_pair_for_driver(self, driver: str):
        return cmd_pair_for_driver(driver)

    def set_connected(self, connected: bool):
        set_binary_detection(
            self,
            'ST',
            connected,
            cmd_pair=CONNECTED,
            timers=self._timers,
            timer_lock=self._timer_lock,
            timeout_sec=0,
            on_timeout=self._timeout_clear,
        )

    def set_detection_type(self, detect_type: str, active: bool):
        if self._camera and not camera_supports_smart_type(self._camera, detect_type):
            return
        mapping = lookup_detection(detect_type)
        if not mapping:
            return
        driver, cmd_pair = mapping
        if driver not in self._allowed:
            return
        timeout = self._ctrl.detection_timeout if self._ctrl else 0
        set_binary_detection(
            self,
            driver,
            active,
            cmd_pair=cmd_pair,
            timers=self._timers,
            timer_lock=self._timer_lock,
            timeout_sec=timeout,
            on_timeout=self._timeout_clear,
        )

    def set_motion(self, active: bool):
        self.set_detection_type('motion', active)

    def set_smart(self, obj_type: str, active: bool):
        self.set_detection_type(obj_type, active)

    def clear_detections(self):
        with self._timer_lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        for driver in self._allowed:
            cmd_pair = self._cmd_pair_for_driver(driver)
            set_binary_detection(
                self,
                driver,
                False,
                cmd_pair=cmd_pair,
                timers=self._timers,
                timer_lock=self._timer_lock,
                timeout_sec=0,
                on_timeout=self._timeout_clear,
                force=True,
            )

    def query(self, command=None):
        if self._ctrl and self._ctrl._client:
            self._ctrl._async.submit(self._refresh())
        else:
            self.reportDrivers()

    async def _refresh(self):
        try:
            cam = await self._ctrl._client.get_camera(self.camera_id)
            self._camera = cam
            self.set_connected(cam.get('state', '') == 'CONNECTED')
            self.reportDrivers()
        except Exception as e:
            LOGGER.warning(f'{self.name}: query refresh failed: {e}')
            self.reportDrivers()

    commands = {
        'QUERY': query,
    }
