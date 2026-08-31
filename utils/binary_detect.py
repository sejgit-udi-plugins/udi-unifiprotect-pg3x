"""Ephemeral binary detection with ISY control (reportCmd) support."""

from __future__ import annotations

import threading
from typing import Callable, Optional, Tuple

import udi_interface

LOGGER = udi_interface.LOGGER

CmdPair = Tuple[str, str]


def driver_is_on(node: udi_interface.Node, driver: str) -> bool:
    try:
        return bool(node.getDriver(driver))
    except Exception:
        return False


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
    """Set a detection driver and emit control commands on transitions."""
    was_on = driver_is_on(node, driver)
    node.setDriver(driver, 1 if active else 0, report=True, force=force)

    if cmd_pair:
        on_cmd, off_cmd = cmd_pair
        if active and not was_on:
            node.reportCmd(on_cmd)
        elif not active and was_on:
            node.reportCmd(off_cmd)

    with timer_lock:
        existing = timers.pop(driver, None)
        if existing:
            existing.cancel()
        if active and timeout_sec > 0:
            timer = threading.Timer(timeout_sec, on_timeout, args=(driver,))
            timer.daemon = True
            timers[driver] = timer
            timer.start()
