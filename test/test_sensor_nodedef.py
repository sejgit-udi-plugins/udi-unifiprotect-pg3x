"""Tests for sensor nodedef selection."""

from utils import sensor_state
from utils.sensor_nodedef import (
    NODEDEF_CONTACT,
    NODEDEF_ENV,
    NODEDEF_GLASS,
    NODEDEF_LEAK,
    NODEDEF_MOTION,
    sensor_nodedef_for_caps,
)


def test_contact_sensor():
    caps = {sensor_state.CAP_OPEN, sensor_state.CAP_TAMPER}
    assert sensor_nodedef_for_caps(caps) == NODEDEF_CONTACT


def test_motion_sensor():
    caps = {sensor_state.CAP_MOTION, sensor_state.CAP_TAMPER}
    assert sensor_nodedef_for_caps(caps) == NODEDEF_MOTION


def test_leak_sensor():
    caps = {sensor_state.CAP_WATER_LEAK, sensor_state.CAP_TAMPER}
    assert sensor_nodedef_for_caps(caps) == NODEDEF_LEAK


def test_glass_sensor():
    caps = {sensor_state.CAP_GLASS, sensor_state.CAP_MOTION}
    assert sensor_nodedef_for_caps(caps) == NODEDEF_GLASS


def test_env_sensor():
    caps = {
        sensor_state.CAP_TEMPERATURE,
        sensor_state.CAP_HUMIDITY,
        sensor_state.CAP_MOTION,
    }
    assert sensor_nodedef_for_caps(caps) == NODEDEF_ENV
