"""Tests for camera detection type lookup."""

from utils.camera_layouts import lookup_detection, normalize_detect_type


def test_normalize_detect_type():
    assert normalize_detect_type('license_plate') == 'licenseplate'
    assert normalize_detect_type('car-horn') == 'carhorn'


def test_lookup_person_and_ring():
    assert lookup_detection('person') == ('GV2', ('PERSON', 'NOPERSON'))
    assert lookup_detection('ring') == ('GV18', ('RING', 'NORING'))


def test_lookup_audio_types():
    assert lookup_detection('smoke')[0] == 'GV9'
    assert lookup_detection('glassBreak')[0] == 'GV14'
    assert lookup_detection('alrmSiren') == ('GV11', ('SIREN', 'NOSIREN'))
    assert lookup_detection('alrmSmoke') == ('GV9', ('SMOKE', 'NOSMOKE'))
    assert lookup_detection('alrmSpeak') == ('GV15', ('SPEAK', 'NOSPEAK'))
    assert lookup_detection('alrmGlassBreak') == ('GV14', ('GLASS', 'NOGLASS'))
