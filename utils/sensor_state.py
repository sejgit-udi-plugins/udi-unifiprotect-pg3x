"""Parse UniFi Protect public API sensor payloads."""

from typing import Any, Optional

# Capability keys aligned with PublicSensorFeatureFlags / SensorFeatureCapability.
CAP_TEMPERATURE = 'temperature'
CAP_HUMIDITY = 'humidity'
CAP_LIGHT = 'light'
CAP_MOTION = 'motion'
CAP_WATER_LEAK = 'water_leak'
CAP_OPEN = 'open'
CAP_TAMPER = 'tamper'
CAP_SMOKE = 'smoke'
CAP_GLASS = 'glass_break'

_MOUNT_CONTACT = frozenset({'door', 'window', 'garage'})


def _nested(data: dict, *path: str) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _feature_flags(sensor: dict) -> Optional[dict]:
    flags = sensor.get('featureFlags')
    if isinstance(flags, dict):
        return flags
    return None


def has_capability(sensor: dict, capability: str) -> bool:
    """Return whether the sensor advertises a capability.

    When ``featureFlags`` is absent (older Protect), fall back to mount type
    and per-metric settings so USL/UP Sense devices still work.
    """
    flags = _feature_flags(sensor)
    if flags is not None:
        return flags.get(capability) is not None

    mount = (sensor.get('mountType') or 'none').lower()
    if capability == CAP_OPEN:
        return mount in _MOUNT_CONTACT
    if capability == CAP_WATER_LEAK:
        leak = _nested(sensor, 'leakSettings') or {}
        return mount == 'leak' or bool(
            leak.get('isInternalEnabled') or leak.get('isExternalEnabled'))
    if capability == CAP_MOTION:
        if mount == 'leak':
            return False
        return bool(_nested(sensor, 'motionSettings', 'isEnabled'))
    if capability == CAP_TEMPERATURE:
        return mount != 'leak' and bool(
            _nested(sensor, 'temperatureSettings', 'isEnabled'))
    if capability == CAP_HUMIDITY:
        return mount != 'leak' and bool(
            _nested(sensor, 'humiditySettings', 'isEnabled'))
    if capability == CAP_LIGHT:
        return mount != 'leak' and bool(_nested(sensor, 'lightSettings', 'isEnabled'))
    if capability == CAP_SMOKE:
        return mount != 'leak' and bool(_nested(sensor, 'alarmSettings', 'isEnabled'))
    if capability == CAP_TAMPER:
        return True
    if capability == CAP_GLASS:
        return bool(_nested(sensor, 'glassBreakSettings', 'isEnabled'))
    return False


def metric_value(sensor: dict, metric: str) -> Optional[float]:
    stats = sensor.get('stats') or {}
    block = stats.get(metric) or {}
    value = block.get('value')
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_leak_detected(sensor: dict) -> bool:
    return sensor.get('leakDetectedAt') is not None or (
        sensor.get('externalLeakDetectedAt') is not None)


def is_tampering_detected(sensor: dict) -> bool:
    return sensor.get('tamperingDetectedAt') is not None


def is_alarm_triggered(sensor: dict) -> bool:
    return sensor.get('alarmTriggeredAt') is not None


def is_connected(sensor: dict) -> bool:
    return (sensor.get('state') or '').upper() == 'CONNECTED'


def contact_open(sensor: dict) -> bool:
    opened = sensor.get('isOpened')
    return bool(opened) if opened is not None else False
