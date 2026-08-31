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


def test_partial_stats_update_keeps_full_capabilities():
    full = {
        'mountType': 'none',
        'featureFlags': {
            'temperature': {'channelCount': 1},
            'humidity': {'channelCount': 1},
            'light': {'channelCount': 1},
        },
    }
    partial = {'stats': {'humidity': {'value': 55.0}}}
    merged = sensor_state.merge_sensor_state(full, partial)
    caps = sensor_capabilities(merged)
    assert sensor_state.CAP_TEMPERATURE in caps
    assert sensor_state.CAP_HUMIDITY in caps
    assert sensor_state.CAP_LIGHT in caps


def test_capability_config_changed():
    from utils.sensor_caps import capability_config_changed

    assert capability_config_changed({'featureFlags': {}})
    assert not capability_config_changed({'stats': {'humidity': {'value': 1}}})
    assert not capability_config_changed({'isOpened': True})


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
