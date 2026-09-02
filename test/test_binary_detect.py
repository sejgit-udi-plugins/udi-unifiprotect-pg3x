"""Tests for binary detection helper."""

from unittest.mock import MagicMock

from utils.binary_detect import set_binary_detection


def test_set_binary_detection_fires_on_cmd():
    node = MagicMock()
    node.setDriver.return_value = True
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', True,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.setDriver.assert_called_once_with('GV1', 1, report=True, force=False)
    node.reportCmd.assert_called_once_with('MOTION', 1, 2)


def test_set_binary_detection_fires_off_cmd():
    node = MagicMock()
    node.setDriver.return_value = True
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', False,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.reportCmd.assert_called_once_with('NOMOTION', 0, 2)


def test_set_binary_detection_no_duplicate_on():
    node = MagicMock()
    node.setDriver.return_value = False
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', True,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.reportCmd.assert_not_called()


def test_set_binary_detection_skips_cmd_when_unchanged():
    node = MagicMock()
    node.setDriver.return_value = False
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV8', False,
        cmd_pair=('LINE', 'NOLINE'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.reportCmd.assert_not_called()
