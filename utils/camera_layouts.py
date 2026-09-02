"""Driver and control-command layout per camera nodedef."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

CmdPair = Tuple[str, str]

# Normalized smartDetectTypes / smartDetectAudioTypes -> (driver, ON/OFF cmds)
SMART_TYPE_MAP: Dict[str, Tuple[str, CmdPair]] = {
    'motion': ('GV1', ('MOTION', 'NOMOTION')),
    'person': ('GV2', ('PERSON', 'NOPERSON')),
    'vehicle': ('GV3', ('VEHICLE', 'NOVEHICLE')),
    'animal': ('GV4', ('ANIMAL', 'NOANIMAL')),
    'package': ('GV5', ('PACKAGE', 'NOPACKAGE')),
    'face': ('GV6', ('FACE', 'NOFACE')),
    'licenseplate': ('GV7', ('LPR', 'NOLPR')),
    'line': ('GV8', ('LINE', 'NOLINE')),
    'linecrossing': ('GV8', ('LINE', 'NOLINE')),
    'smartdetectline': ('GV8', ('LINE', 'NOLINE')),
    'smoke': ('GV9', ('SMOKE', 'NOSMOKE')),
    'cmonx': ('GV10', ('CO', 'NOCO')),
    'co': ('GV10', ('CO', 'NOCO')),
    'siren': ('GV11', ('SIREN', 'NOSIREN')),
    'babycry': ('GV12', ('BABYCRY', 'NOBABYCRY')),
    'carhorn': ('GV13', ('HORN', 'NOHORN')),
    'car_horn': ('GV13', ('HORN', 'NOHORN')),
    'glassbreak': ('GV14', ('GLASS', 'NOGLASS')),
    'glass_break': ('GV14', ('GLASS', 'NOGLASS')),
    'speak': ('GV15', ('SPEAK', 'NOSPEAK')),
    'bark': ('GV16', ('BARK', 'NOBARK')),
    'burglar': ('GV17', ('CARALRM', 'NOCARALRM')),
    'ring': ('GV18', ('RING', 'NORING')),
}


def normalize_detect_type(value: str) -> str:
    """Normalize Protect smartDetectTypes / smartDetectAudioTypes strings."""
    s = str(value).lower().replace('_', '').replace('-', '')
    # Events use alrmSmoke, alrmSiren, alrmSpeak, etc.
    if s.startswith('alrm'):
        s = s[4:]
    return s


def lookup_detection(value: str) -> Optional[Tuple[str, CmdPair]]:
    return SMART_TYPE_MAP.get(normalize_detect_type(value))


def cmd_pair_for_driver(driver: str) -> Optional[CmdPair]:
    for drv, pair in SMART_TYPE_MAP.values():
        if drv == driver:
            return pair
    return None


CAMERA_DRIVERS = {
    'unifi_camera_detect': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
    ],
    'unifi_camera_ai': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
        {'driver': 'GV6', 'value': 0, 'uom': 2},
        {'driver': 'GV7', 'value': 0, 'uom': 2},
        {'driver': 'GV8', 'value': 0, 'uom': 2},
    ],
    'unifi_camera_ai_audio': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
        {'driver': 'GV6', 'value': 0, 'uom': 2},
        {'driver': 'GV7', 'value': 0, 'uom': 2},
        {'driver': 'GV8', 'value': 0, 'uom': 2},
        {'driver': 'GV9', 'value': 0, 'uom': 2},
        {'driver': 'GV10', 'value': 0, 'uom': 2},
        {'driver': 'GV11', 'value': 0, 'uom': 2},
        {'driver': 'GV12', 'value': 0, 'uom': 2},
        {'driver': 'GV13', 'value': 0, 'uom': 2},
        {'driver': 'GV14', 'value': 0, 'uom': 2},
        {'driver': 'GV15', 'value': 0, 'uom': 2},
        {'driver': 'GV16', 'value': 0, 'uom': 2},
        {'driver': 'GV17', 'value': 0, 'uom': 2},
    ],
    'unifi_camera_doorbell': [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
        {'driver': 'GV4', 'value': 0, 'uom': 2},
        {'driver': 'GV5', 'value': 0, 'uom': 2},
        {'driver': 'GV6', 'value': 0, 'uom': 2},
        {'driver': 'GV18', 'value': 0, 'uom': 2},
    ],
}

DETECTION_DRIVERS_BY_NODEDEF = {
    nodedef: tuple(d['driver'] for d in defs if d['driver'] != 'ST')
    for nodedef, defs in CAMERA_DRIVERS.items()
}

CAMERA_SENDS = {
    'unifi_camera_detect': (
        'MOTION', 'NOMOTION', 'PERSON', 'NOPERSON', 'VEHICLE', 'NOVEHICLE',
        'ANIMAL', 'NOANIMAL', 'PACKAGE', 'NOPACKAGE',
    ),
    'unifi_camera_ai': (
        'MOTION', 'NOMOTION', 'PERSON', 'NOPERSON', 'VEHICLE', 'NOVEHICLE',
        'ANIMAL', 'NOANIMAL', 'PACKAGE', 'NOPACKAGE', 'FACE', 'NOFACE',
        'LPR', 'NOLPR', 'LINE', 'NOLINE',
    ),
    'unifi_camera_ai_audio': (
        'MOTION', 'NOMOTION', 'PERSON', 'NOPERSON', 'VEHICLE', 'NOVEHICLE',
        'ANIMAL', 'NOANIMAL', 'PACKAGE', 'NOPACKAGE', 'FACE', 'NOFACE',
        'LPR', 'NOLPR', 'LINE', 'NOLINE', 'SMOKE', 'NOSMOKE', 'CO', 'NOCO',
        'SIREN', 'NOSIREN', 'BABYCRY', 'NOBABYCRY', 'HORN', 'NOHORN',
        'GLASS', 'NOGLASS', 'SPEAK', 'NOSPEAK', 'BARK', 'NOBARK',
        'CARALRM', 'NOCARALRM',
    ),
    'unifi_camera_doorbell': (
        'MOTION', 'NOMOTION', 'PERSON', 'NOPERSON', 'VEHICLE', 'NOVEHICLE',
        'ANIMAL', 'NOANIMAL', 'PACKAGE', 'NOPACKAGE', 'FACE', 'NOFACE', 'RING', 'NORING',
    ),
}
