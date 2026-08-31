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


def sensor_capabilities(sensor: dict) -> set:
    return {cap for cap in ALL_CAPABILITIES if sensor_state.has_capability(sensor, cap)}
