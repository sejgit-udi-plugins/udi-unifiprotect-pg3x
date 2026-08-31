"""UniFi Protect USL / UP Sense sensor node."""

import threading

import udi_interface

from utils import sensor_state

LOGGER = udi_interface.LOGGER


class Sensor(udi_interface.Node):
    id = 'unifi_sensor'

    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},   # Motion
        {'driver': 'GV2', 'value': 0, 'uom': 2},   # Contact open
        {'driver': 'GV3', 'value': 0, 'uom': 2},   # Leak / wet
        {'driver': 'GV4', 'value': 0, 'uom': 2},   # Tamper
        {'driver': 'GV5', 'value': 0, 'uom': 2},   # Alarm / smoke
        {'driver': 'GV6', 'value': 0, 'uom': 2},   # Glass break
        {'driver': 'CV1', 'value': 0, 'uom': 4},   # Temperature °C
        {'driver': 'CV2', 'value': 0, 'uom': 22},  # Humidity %
        {'driver': 'CV3', 'value': 0, 'uom': 36},  # Light lux
    ]

    BINARY_DRIVERS = ('GV1', 'GV2', 'GV3', 'GV4', 'GV5', 'GV6')

    def __init__(self, polyglot, primary, address, name, sensor_id, controller):
        super().__init__(polyglot, primary, address, name)
        self.sensor_id = sensor_id
        self._ctrl = controller
        self._timers = {}
        self._timer_lock = threading.Lock()
        self._caps = set()
        self._state: dict = {}

    def _set_bin(self, driver, active: bool):
        self.setDriver(driver, 1 if active else 0, report=True, force=False)

    def _set_num(self, driver, value: float):
        self.setDriver(driver, value, report=True, force=False)

    def set_capabilities(self, caps: set):
        self._caps = caps

    def apply_state(self, sensor: dict, *, replace: bool = False):
        if replace or not self._state:
            self._state = dict(sensor)
        else:
            self._state = sensor_state.merge_sensor_state(self._state, sensor)
        data = self._state

        if 'state' in sensor or replace:
            self.set_connected(sensor_state.is_connected(data))

        if sensor_state.CAP_MOTION in self._caps and 'isMotionDetected' in sensor:
            self._set_bin('GV1', bool(data.get('isMotionDetected')))
        if sensor_state.CAP_OPEN in self._caps and 'isOpened' in sensor:
            self._set_bin('GV2', sensor_state.contact_open(data))
        if sensor_state.CAP_WATER_LEAK in self._caps and (
                'leakDetectedAt' in sensor or 'externalLeakDetectedAt' in sensor):
            self._set_bin('GV3', sensor_state.is_leak_detected(data))
        if sensor_state.CAP_TAMPER in self._caps and 'tamperingDetectedAt' in sensor:
            self._set_bin('GV4', sensor_state.is_tampering_detected(data))
        if sensor_state.CAP_SMOKE in self._caps and 'alarmTriggeredAt' in sensor:
            self._set_bin('GV5', sensor_state.is_alarm_triggered(data))

        stats = sensor.get('stats')
        if isinstance(stats, dict):
            if sensor_state.CAP_TEMPERATURE in self._caps:
                temp = sensor_state.metric_value(data, 'temperature')
                if temp is not None and 'temperature' in stats:
                    self._set_num('CV1', temp)
            if sensor_state.CAP_HUMIDITY in self._caps:
                hum = sensor_state.metric_value(data, 'humidity')
                if hum is not None and 'humidity' in stats:
                    self._set_num('CV2', hum)
            if sensor_state.CAP_LIGHT in self._caps:
                light = sensor_state.metric_value(data, 'light')
                if light is not None and 'light' in stats:
                    self._set_num('CV3', light)
        elif replace:
            temp = sensor_state.metric_value(data, 'temperature')
            if sensor_state.CAP_TEMPERATURE in self._caps and temp is not None:
                self._set_num('CV1', temp)
            hum = sensor_state.metric_value(data, 'humidity')
            if sensor_state.CAP_HUMIDITY in self._caps and hum is not None:
                self._set_num('CV2', hum)
            light = sensor_state.metric_value(data, 'light')
            if sensor_state.CAP_LIGHT in self._caps and light is not None:
                self._set_num('CV3', light)

    def set_connected(self, connected: bool):
        self._set_bin('ST', connected)

    def set_motion(self, active: bool):
        if sensor_state.CAP_MOTION in self._caps:
            self._set_detection('GV1', active)

    def set_glass_break(self, active: bool):
        if sensor_state.CAP_GLASS in self._caps:
            self._set_detection('GV6', active)

    def _set_detection(self, driver, active: bool):
        self._set_bin(driver, active)
        timeout = self._ctrl.detection_timeout if self._ctrl else 0
        with self._timer_lock:
            existing = self._timers.pop(driver, None)
            if existing:
                existing.cancel()
            if active and timeout > 0:
                timer = threading.Timer(timeout, self._timeout_clear, args=(driver,))
                timer.daemon = True
                self._timers[driver] = timer
                timer.start()

    def _timeout_clear(self, driver):
        with self._timer_lock:
            self._timers.pop(driver, None)
        LOGGER.warning(
            f'{self.name}: {driver} auto-cleared after '
            f'{self._ctrl.detection_timeout}s (no close event received)')
        self._set_bin(driver, False)

    def clear_detections(self):
        with self._timer_lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        for driver in self.BINARY_DRIVERS:
            self.setDriver(driver, 0, report=True, force=True)

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
