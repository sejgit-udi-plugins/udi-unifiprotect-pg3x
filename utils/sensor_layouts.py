"""Driver and control-command layout per sensor nodedef."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from utils import sensor_state

CmdPair = Tuple[str, str]
Layout = Dict[str, Tuple[str, Optional[CmdPair]]]

CONTACT_LAYOUT: Layout = {
    sensor_state.CAP_OPEN: ('GV1', ('OPEN', 'CLOSED')),
    sensor_state.CAP_TAMPER: ('GV2', ('TAMPER', 'NOTAMPER')),
}

MOTION_LAYOUT: Layout = {
    sensor_state.CAP_MOTION: ('GV1', ('MOTION', 'NOMOTION')),
    sensor_state.CAP_TAMPER: ('GV2', ('TAMPER', 'NOTAMPER')),
}

LEAK_LAYOUT: Layout = {
    sensor_state.CAP_WATER_LEAK: ('GV1', ('LEAK', 'NOLEAK')),
    sensor_state.CAP_TAMPER: ('GV2', ('TAMPER', 'NOTAMPER')),
}

GLASS_LAYOUT: Layout = {
    sensor_state.CAP_MOTION: ('GV1', ('MOTION', 'NOMOTION')),
    sensor_state.CAP_GLASS: ('GV2', ('GLASS', 'NOGLASS')),
    sensor_state.CAP_TAMPER: ('GV3', ('TAMPER', 'NOTAMPER')),
}

ENV_LAYOUT: Layout = {
    sensor_state.CAP_MOTION: ('GV1', ('MOTION', 'NOMOTION')),
    sensor_state.CAP_OPEN: ('GV2', ('OPEN', 'CLOSED')),
    sensor_state.CAP_WATER_LEAK: ('GV3', ('LEAK', 'NOLEAK')),
    sensor_state.CAP_TAMPER: ('GV4', ('TAMPER', 'NOTAMPER')),
    sensor_state.CAP_SMOKE: ('GV5', ('ALARM', 'NOALARM')),
    sensor_state.CAP_GLASS: ('GV6', ('GLASS', 'NOGLASS')),
}

SENSOR_LAYOUTS = {
    'unifi_sensor_contact': CONTACT_LAYOUT,
    'unifi_sensor_motion': MOTION_LAYOUT,
    'unifi_sensor_leak': LEAK_LAYOUT,
    'unifi_sensor_glass': GLASS_LAYOUT,
    'unifi_sensor_env': ENV_LAYOUT,
}

SENSOR_DRIVERS = {
    'unifi_sensor_contact': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
    ],
    'unifi_sensor_motion': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
    ],
    'unifi_sensor_leak': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
    ],
    'unifi_sensor_glass': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
    ],
    'unifi_sensor_env': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
        {'driver': 'GV6', 'value': 0, 'uom': 2},
        {'driver': 'CV1', 'value': 0, 'uom': 4},
        {'driver': 'CV2', 'value': 0, 'uom': 22},
        {'driver': 'CV3', 'value': 0, 'uom': 36},
    ],
}

SENSOR_SENDS = {
    'unifi_sensor_contact': ('OPEN', 'CLOSED', 'TAMPER', 'NOTAMPER'),
    'unifi_sensor_motion': ('MOTION', 'NOMOTION', 'TAMPER', 'NOTAMPER'),
    'unifi_sensor_leak': ('LEAK', 'NOLEAK', 'TAMPER', 'NOTAMPER'),
    'unifi_sensor_glass': ('MOTION', 'NOMOTION', 'GLASS', 'NOGLASS', 'TAMPER', 'NOTAMPER'),
    'unifi_sensor_env': (
        'MOTION', 'NOMOTION', 'OPEN', 'CLOSED', 'LEAK', 'NOLEAK',
        'TAMPER', 'NOTAMPER', 'ALARM', 'NOALARM', 'GLASS', 'NOGLASS',
    ),
}
