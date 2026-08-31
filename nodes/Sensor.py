"""UniFi Protect USL / UP Sense sensor node."""

from __future__ import annotations

import threading
from copy import deepcopy

import udi_interface

from utils import sensor_state
from utils.binary_detect import set_binary_detection
from utils.sensor_layouts import SENSOR_DRIVERS, SENSOR_LAYOUTS
from utils.temperature import celsius_to_display, temp_uom

LOGGER = udi_interface.LOGGER


class Sensor(udi_interface.Node):
    id = 'unifi_sensor_contact'

    drivers = SENSOR_DRIVERS['unifi_sensor_contact']

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        sensor_id,
        controller,
        nodedef_id: str,
    ):
        self.id = nodedef_id
        self.drivers = deepcopy(SENSOR_DRIVERS[nodedef_id])
        super().__init__(polyglot, primary, address, name)
        self.sensor_id = sensor_id
        self._ctrl = controller
        self._layout = SENSOR_LAYOUTS[nodedef_id]
        self._timers = {}
        self._timer_lock = threading.Lock()
        self._caps = set()
        self._state: dict = {}

    def _driver_for_cap(self, cap: str):
        entry = self._layout.get(cap)
        return entry[0] if entry else None

    def _cmd_pair_for_cap(self, cap: str):
        entry = self._layout.get(cap)
        return entry[1] if entry else None

    def _timeout_clear(self, driver: str):
        cap = self._cap_for_driver(driver)
        cmd_pair = self._cmd_pair_for_cap(cap) if cap else None
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

    def _cap_for_driver(self, driver: str):
        for cap, (drv, _pair) in self._layout.items():
            if drv == driver:
                return cap
        return None

    def _apply_binary(self, cap: str, active: bool, *, ephemeral: bool = False):
        if cap not in self._caps:
            return
        driver = self._driver_for_cap(cap)
        if not driver:
            return
        cmd_pair = self._cmd_pair_for_cap(cap)
        timeout = self._ctrl.detection_timeout if ephemeral and self._ctrl else 0
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

    def set_capabilities(self, caps: set):
        self._caps = caps

    def apply_state(self, sensor: dict, *, replace: bool = False):
        if replace or not self._state:
            self._state = dict(sensor)
        else:
            self._state = sensor_state.merge_sensor_state(self._state, sensor)
        data = self._state

        if 'state' in sensor or replace:
            connected = sensor_state.is_connected(data)
            set_binary_detection(
                self,
                'ST',
                connected,
                cmd_pair=None,
                timers=self._timers,
                timer_lock=self._timer_lock,
                timeout_sec=0,
                on_timeout=self._timeout_clear,
            )

        if sensor_state.CAP_MOTION in self._caps and 'isMotionDetected' in sensor:
            self._apply_binary(sensor_state.CAP_MOTION, bool(data.get('isMotionDetected')))
        if sensor_state.CAP_OPEN in self._caps and 'isOpened' in sensor:
            self._apply_binary(sensor_state.CAP_OPEN, sensor_state.contact_open(data))
        if sensor_state.CAP_WATER_LEAK in self._caps and (
                'leakDetectedAt' in sensor or 'externalLeakDetectedAt' in sensor):
            self._apply_binary(sensor_state.CAP_WATER_LEAK, sensor_state.is_leak_detected(data))
        if sensor_state.CAP_TAMPER in self._caps and 'tamperingDetectedAt' in sensor:
            self._apply_binary(sensor_state.CAP_TAMPER, sensor_state.is_tampering_detected(data))
        if sensor_state.CAP_SMOKE in self._caps and 'alarmTriggeredAt' in sensor:
            self._apply_binary(sensor_state.CAP_SMOKE, sensor_state.is_alarm_triggered(data))

        stats = sensor.get('stats')
        units = self._ctrl.temperature_units if self._ctrl else 'F'
        temp_u = temp_uom(units)
        if isinstance(stats, dict):
            if sensor_state.CAP_TEMPERATURE in self._caps:
                temp = sensor_state.metric_value(data, 'temperature')
                if temp is not None and 'temperature' in stats:
                    self.setDriver(
                        'CV1',
                        celsius_to_display(temp, units),
                        report=True,
                        force=False,
                        uom=temp_u,
                    )
            if sensor_state.CAP_HUMIDITY in self._caps:
                hum = sensor_state.metric_value(data, 'humidity')
                if hum is not None and 'humidity' in stats:
                    self.setDriver('CV2', hum, report=True, force=False)
            if sensor_state.CAP_LIGHT in self._caps:
                light = sensor_state.metric_value(data, 'light')
                if light is not None and 'light' in stats:
                    self.setDriver('CV3', light, report=True, force=False)
        elif replace:
            temp = sensor_state.metric_value(data, 'temperature')
            if sensor_state.CAP_TEMPERATURE in self._caps and temp is not None:
                self.setDriver(
                    'CV1',
                    celsius_to_display(temp, units),
                    report=True,
                    force=False,
                    uom=temp_u,
                )
            hum = sensor_state.metric_value(data, 'humidity')
            if sensor_state.CAP_HUMIDITY in self._caps and hum is not None:
                self.setDriver('CV2', hum, report=True, force=False)
            light = sensor_state.metric_value(data, 'light')
            if sensor_state.CAP_LIGHT in self._caps and light is not None:
                self.setDriver('CV3', light, report=True, force=False)

    def set_motion(self, active: bool):
        self._apply_binary(sensor_state.CAP_MOTION, active, ephemeral=True)

    def set_glass_break(self, active: bool):
        self._apply_binary(sensor_state.CAP_GLASS, active, ephemeral=True)

    def clear_detections(self):
        with self._timer_lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        for cap, (driver, cmd_pair) in self._layout.items():
            if driver == 'ST':
                continue
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
            data = await self._ctrl._client.get_sensor(self.sensor_id)
            self.apply_state(data, replace=True)
            self.reportDrivers()
        except Exception as e:
            LOGGER.warning(f'{self.name}: query refresh failed: {e}')
            self.reportDrivers()

    commands = {
        'QUERY': query,
    }
