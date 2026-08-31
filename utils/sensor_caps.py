"""Build capability sets for Protect sensors."""

from utils import sensor_state

ALL_CAPABILITIES = (
    sensor_state.CAP_TEMPERATURE,
    sensor_state.CAP_HUMIDITY,
    sensor_state.CAP_LIGHT,
    sensor_state.CAP_MOTION,
    sensor_state.CAP_WATER_LEAK,
    sensor_state.CAP_OPEN,
    sensor_state.CAP_TAMPER,
    sensor_state.CAP_SMOKE,
    sensor_state.CAP_GLASS,
)

CAPABILITY_CONFIG_KEYS = frozenset({
    'featureFlags',
    'mountType',
    'temperatureSettings',
    'humiditySettings',
    'lightSettings',
    'motionSettings',
    'leakSettings',
    'alarmSettings',
    'glassBreakSettings',
})


def capability_config_changed(update: dict) -> bool:
    """Return True when an update may change advertised sensor capabilities."""
    return any(key in update for key in CAPABILITY_CONFIG_KEYS)


def sensor_capabilities(sensor: dict) -> set:
    return {cap for cap in ALL_CAPABILITIES if sensor_state.has_capability(sensor, cap)}
