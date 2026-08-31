"""Temperature unit helpers for ISY display."""

from __future__ import annotations

UOM_CELSIUS = 4
UOM_FAHRENHEIT = 17


def normalize_units(units: str) -> str:
    value = (units or 'F').strip().upper()
    return 'C' if value == 'C' else 'F'


def temp_uom(units: str) -> int:
    return UOM_CELSIUS if normalize_units(units) == 'C' else UOM_FAHRENHEIT


def celsius_to_display(celsius: float, units: str) -> float:
    if normalize_units(units) == 'F':
        return round((celsius * 9.0 / 5.0) + 32.0, 1)
    return round(celsius, 1)
