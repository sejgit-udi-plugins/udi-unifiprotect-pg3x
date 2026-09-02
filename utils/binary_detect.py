"""Ephemeral binary detection with ISY control (reportCmd) support."""

from __future__ import annotations

import threading
from typing import Callable, Optional, Tuple

import udi_interface

LOGGER = udi_interface.LOGGER

CmdPair = Tuple[str, str]


def _emit_control(
    node: udi_interface.Node, cmd: str, driver: str, active: bool
) -> None:
    """Send an ISY control command with value and uom (required by udi_interface)."""
    value = 1 if active else 0
    LOGGER.info(f'{node.name}: reportCmd {cmd} ({driver}) value={value}')
    node.reportCmd(cmd, value, 2)


def set_binary_detection(
    node: udi_interface.Node,
    driver: str,
    active: bool,
    *,
    cmd_pair: Optional[CmdPair] = None,
    timers: dict,
    timer_lock: threading.Lock,
    timeout_sec: int,
    on_timeout: Callable[[str], None],
    force: bool = False,
) -> None:
    """Set a detection driver and emit control commands when the value changes."""
    changed = node.setDriver(
        driver, 1 if active else 0, report=True, force=force)

    if cmd_pair and changed:
        on_cmd, off_cmd = cmd_pair
        if active:
            _emit_control(node, on_cmd, driver, True)
        else:
            _emit_control(node, off_cmd, driver, False)

    with timer_lock:
        existing = timers.pop(driver, None)
        if existing:
            existing.cancel()
        if active and timeout_sec > 0:
            timer = threading.Timer(timeout_sec, on_timeout, args=(driver,))
            timer.daemon = True
            timers[driver] = timer
            timer.start()
