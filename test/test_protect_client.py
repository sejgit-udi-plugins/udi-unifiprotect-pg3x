"""Tests for Protect integration API helpers."""

from utils.protect_client import camera_address, unwrap_api_payload


def test_unwrap_api_payload_list():
    assert unwrap_api_payload([{'id': 'a'}]) == [{'id': 'a'}]


def test_unwrap_api_payload_data_wrapper():
    assert unwrap_api_payload({'data': [{'id': 'a'}]}) == [{'id': 'a'}]


def test_camera_address_from_mac():
    cam = {'id': 'abc', 'mac': 'AA:BB:CC:DD:EE:FF'}
    assert camera_address(cam) == 'aabbccddeeff'


def test_camera_address_fallback_id():
    cam = {'id': 'camera-uuid-here', 'mac': ''}
    assert camera_address(cam) == 'camerauuidhe'
