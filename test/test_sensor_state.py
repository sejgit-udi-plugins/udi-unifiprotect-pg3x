"""Tests for sensor capability and state parsing."""

from utils.sensor_caps import sensor_capabilities
from utils import sensor_state


def test_leak_detected_from_timestamp():
    assert sensor_state.is_leak_detected({'leakDetectedAt': 123})
    assert not sensor_state.is_leak_detected({'leakDetectedAt': None})


def test_metric_value_from_stats():
    sensor = {
        'stats': {
            'temperature': {'value': 21.5},
            'humidity': {'value': 44},
        },
    }
    assert sensor_state.metric_value(sensor, 'temperature') == 21.5
    assert sensor_state.metric_value(sensor, 'humidity') == 44.0
    assert sensor_state.metric_value(sensor, 'light') is None


def test_merge_preserves_connection_on_partial_update():
    base = {
        'state': 'CONNECTED',
        'isOpened': True,
        'stats': {'temperature': {'value': 21.0}},
    }
    update = {'stats': {'humidity': {'value': 44.0}}}
    merged = sensor_state.merge_sensor_state(base, update)
    assert sensor_state.is_connected(merged)
    assert merged['isOpened'] is True
    assert sensor_state.metric_value(merged, 'temperature') == 21.0
    assert sensor_state.metric_value(merged, 'humidity') == 44.0


def test_feature_flags_gate_temperature():
    sensor = {
        'featureFlags': {'temperature': {'channelCount': 1}},
        'temperatureSettings': {'isEnabled': False},
    }
    assert sensor_state.has_capability(sensor, sensor_state.CAP_TEMPERATURE)


def test_mount_type_fallback_open():
    sensor = {'mountType': 'door'}
    assert sensor_state.has_capability(sensor, sensor_state.CAP_OPEN)


def test_sensor_capabilities_collects_supported():
    sensor = {
        'mountType': 'door',
        'featureFlags': {
            'open': {'channelCount': 1},
            'motion': {'channelCount': 1},
            'tamper': {'channelCount': 1},
        },
        'motionSettings': {'isEnabled': True},
    }
    caps = sensor_capabilities(sensor)
    assert sensor_state.CAP_OPEN in caps
    assert sensor_state.CAP_MOTION in caps
    assert sensor_state.CAP_TAMPER in caps
