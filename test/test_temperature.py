"""Tests for temperature conversion."""

from utils.temperature import celsius_to_display, normalize_units, temp_uom, UOM_CELSIUS, UOM_FAHRENHEIT


def test_normalize_units_defaults_fahrenheit():
    assert normalize_units('') == 'F'
    assert normalize_units('f') == 'F'
    assert normalize_units('C') == 'C'


def test_celsius_to_fahrenheit():
    assert celsius_to_display(0, 'F') == 32.0
    assert celsius_to_display(100, 'C') == 100.0


def test_temp_uom():
    assert temp_uom('C') == UOM_CELSIUS
    assert temp_uom('F') == UOM_FAHRENHEIT
