"""UniFi Protect camera node."""

import threading

import udi_interface

LOGGER = udi_interface.LOGGER


class Camera(udi_interface.Node):
    id = 'unifi_camera'

    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
        {'driver': 'GV6', 'value': 50, 'uom': 51},
        {'driver': 'GV7', 'value': 1, 'uom': 56},
        {'driver': 'GV8', 'value': 0, 'uom': 25},
    ]

    DETECTION_DRIVERS = ('GV1', 'GV2', 'GV3', 'GV4', 'GV5')

    def __init__(self, polyglot, primary, address, name, camera_id, controller):
        super().__init__(polyglot, primary, address, name)
        self.camera_id = camera_id
        self._ctrl = controller
        self._timers = {}
        self._timer_lock = threading.Lock()

    def _set(self, driver, value):
        self.setDriver(driver, 1 if value else 0, report=True, force=False)

    def set_connected(self, connected: bool):
        self._set('ST', connected)

    def set_motion(self, active: bool):
        self._set_detection('GV1', active)

    def set_smart(self, obj_type: str, active: bool):
        mapping = {
            'person': 'GV2',
            'vehicle': 'GV3',
            'animal': 'GV4',
            'package': 'GV5',
        }
        driver = mapping.get(obj_type)
        if driver:
            self._set_detection(driver, active)

    def _set_detection(self, driver, active: bool):
        self._set(driver, active)
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
        self._set(driver, False)

    def clear_detections(self):
        with self._timer_lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        for driver in self.DETECTION_DRIVERS:
            self.setDriver(driver, 0, report=True, force=True)

    def set_speaker(self, speaker: dict):
        self.setDriver('GV6', speaker.get('ringVolume', 0))
        self.setDriver('GV7', speaker.get('repeatTimes', 1))
        ringtone_id = speaker.get('ringtoneId', '')
        ringtones = self._ctrl.ringtones if self._ctrl else []
        idx = next((i for i, r in enumerate(ringtones) if r.get('id') == ringtone_id), 0)
        self.setDriver('GV8', idx)

    def _patch(self, payload: dict):
        if self._ctrl and self._ctrl._client:
            self._ctrl._async.submit(
                self._ctrl._client.patch_camera(self.camera_id, payload))

    def cmd_set_ringtone(self, command):
        idx = int(command.get('value', 0))
        ringtones = self._ctrl.ringtones
        if idx < len(ringtones):
            ringtone_id = ringtones[idx]['id']
            self._patch({'speakerSettings': {'ringtoneId': ringtone_id}})
            self.setDriver('GV8', idx)
            LOGGER.info(f'{self.name}: set ringtone → {ringtones[idx]["name"]}')
        else:
            LOGGER.warning(f'{self.name}: ringtone index {idx} out of range')

    def cmd_set_ring_vol(self, command):
        vol = int(command.get('value', 0))
        self._patch({'speakerSettings': {'ringVolume': vol}})
        self.setDriver('GV6', vol)
        LOGGER.info(f'{self.name}: set ring volume → {vol}')

    def cmd_set_repeat(self, command):
        times = int(command.get('value', 1))
        self._patch({'speakerSettings': {'repeatTimes': times}})
        self.setDriver('GV7', times)
        LOGGER.info(f'{self.name}: set repeat times → {times}')

    def query(self, command=None):
        if self._ctrl and self._ctrl._client:
            self._ctrl._async.submit(self._refresh())
        else:
            self.reportDrivers()

    async def _refresh(self):
        try:
            cam = await self._ctrl._client.get_camera(self.camera_id)
            if cam.get('speakerSettings'):
                self.set_speaker(cam['speakerSettings'])
            self.reportDrivers()
        except Exception as e:
            LOGGER.warning(f'{self.name}: query refresh failed: {e}')
            self.reportDrivers()

    commands = {
        'QUERY': query,
        'SET_RINGTONE': cmd_set_ringtone,
        'SET_RING_VOL': cmd_set_ring_vol,
        'SET_REPEAT': cmd_set_repeat,
    }
