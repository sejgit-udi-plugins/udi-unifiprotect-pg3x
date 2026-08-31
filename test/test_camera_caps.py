"""Tests for camera capability and nodedef selection."""

from utils.camera_caps import (
    NODEDEF_AI,
    NODEDEF_AI_AUDIO,
    NODEDEF_DETECT,
    NODEDEF_DOORBELL,
    camera_nodedef_for,
    camera_supports_smart_type,
)


def test_basic_detect_camera():
    cam = {
        'featureFlags': {
            'smartDetectTypes': ['person', 'vehicle'],
        },
    }
    assert camera_nodedef_for(cam) == NODEDEF_DETECT


def test_ai_camera_with_face():
    cam = {
        'featureFlags': {
            'smartDetectTypes': ['person', 'face'],
        },
    }
    assert camera_nodedef_for(cam) == NODEDEF_AI


def test_ai_audio_camera():
    cam = {
        'featureFlags': {
            'smartDetectTypes': ['person'],
            'smartDetectAudioTypes': ['smoke'],
        },
    }
    assert camera_nodedef_for(cam) == NODEDEF_AI_AUDIO


def test_doorbell_camera():
    cam = {
        'featureFlags': {
            'isDoorbell': True,
            'smartDetectTypes': ['person'],
        },
    }
    assert camera_nodedef_for(cam) == NODEDEF_DOORBELL


def test_supports_line_crossing():
    cam = {'featureFlags': {'hasLineCrossing': True}}
    assert camera_supports_smart_type(cam, 'line')
    assert camera_nodedef_for(cam) == NODEDEF_AI
