"""Map sensor capabilities to ISY nodedef ids."""

from utils import sensor_state

NODEDEF_CONTACT = 'unifi_sensor_contact'
NODEDEF_MOTION = 'unifi_sensor_motion'
NODEDEF_LEAK = 'unifi_sensor_leak'
NODEDEF_GLASS = 'unifi_sensor_glass'
NODEDEF_ENV = 'unifi_sensor_env'


def sensor_nodedef_for_caps(caps: set) -> str:
    """Choose the smallest nodedef that covers the sensor capabilities."""
    if any(c in caps for c in (
            sensor_state.CAP_TEMPERATURE,
            sensor_state.CAP_HUMIDITY,
            sensor_state.CAP_LIGHT,
    )):
        return NODEDEF_ENV
    if sensor_state.CAP_GLASS in caps:
        return NODEDEF_GLASS
    if sensor_state.CAP_WATER_LEAK in caps and sensor_state.CAP_OPEN not in caps:
        return NODEDEF_LEAK
    if sensor_state.CAP_OPEN in caps:
        return NODEDEF_CONTACT
    if sensor_state.CAP_MOTION in caps:
        return NODEDEF_MOTION
    return NODEDEF_CONTACT
