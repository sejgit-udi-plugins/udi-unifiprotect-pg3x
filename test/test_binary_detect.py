"""Tests for binary detection helper."""

from unittest.mock import MagicMock

from utils.binary_detect import set_binary_detection


def test_set_binary_detection_fires_on_cmd():
    node = MagicMock()
    node.getDriver.return_value = 0
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', True,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.setDriver.assert_called_once_with('GV1', 1, report=True, force=False)
    node.reportCmd.assert_called_once_with('MOTION')


def test_set_binary_detection_fires_off_cmd():
    node = MagicMock()
    node.getDriver.return_value = 1
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', False,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.reportCmd.assert_called_once_with('NOMOTION')


def test_set_binary_detection_no_duplicate_on():
    node = MagicMock()
    node.getDriver.return_value = 1
    timers = {}
    lock = MagicMock()

    set_binary_detection(
        node, 'GV1', True,
        cmd_pair=('MOTION', 'NOMOTION'),
        timers=timers, timer_lock=lock,
        timeout_sec=0, on_timeout=MagicMock(),
    )

    node.reportCmd.assert_not_called()
