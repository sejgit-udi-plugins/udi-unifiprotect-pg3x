"""Camera capability helpers for the public Integration API."""

from __future__ import annotations

from typing import Iterable

from utils.camera_layouts import normalize_detect_type

NODEDEF_DETECT = 'unifi_camera_detect'
NODEDEF_AI = 'unifi_camera_ai'
NODEDEF_AI_AUDIO = 'unifi_camera_ai_audio'
NODEDEF_DOORBELL = 'unifi_camera_doorbell'

_BASIC_SMART = frozenset({'person', 'vehicle', 'animal', 'package'})
_AI_SMART = frozenset({'face', 'licenseplate', 'license_plate'})
_AUDIO_SMART = frozenset({
    'smoke', 'cmonx', 'co', 'siren', 'speak', 'babycry',
    'bark', 'burglar', 'carhorn', 'car_horn', 'glassbreak', 'glass_break',
})


def _feature_flags(camera: dict) -> dict:
    flags = camera.get('featureFlags')
    return flags if isinstance(flags, dict) else {}


def _normalize(values: Iterable[str]) -> set:
    return {normalize_detect_type(v) for v in values}


def camera_smart_types(camera: dict) -> set:
    flags = _feature_flags(camera)
    settings = camera.get('smartDetectSettings') or {}
    object_types = flags.get('smartDetectTypes') or settings.get('objectTypes') or []
    return _normalize(object_types)


def camera_audio_types(camera: dict) -> set:
    flags = _feature_flags(camera)
    settings = camera.get('smartDetectSettings') or {}
    audio_types = flags.get('smartDetectAudioTypes') or settings.get('audioTypes') or []
    return _normalize(audio_types)


def camera_has_line_crossing(camera: dict) -> bool:
    flags = _feature_flags(camera)
    if flags.get('hasLineCrossing') or flags.get('hasLineCrossingCounting'):
        return True
    settings = camera.get('smartDetectSettings') or {}
    if settings.get('lines') or settings.get('lineCrossing'):
        return True
    return False


def camera_supports_line_events(camera: dict) -> bool:
    """Whether line-crossing events should be honored for this camera.

    The public Integration API often omits ``hasLineCrossing`` from
    ``featureFlags`` even when lines are configured in Protect. When we cannot
    disprove line support, trust ``smartDetectLine`` events from the stream.
    """
    if camera_has_line_crossing(camera):
        return True
    flags = _feature_flags(camera)
    if flags is None:
        return True
    # Public API returns a trimmed featureFlags object without line-crossing
    # keys; absence of those keys does not mean lines are disabled.
    return True


def camera_is_doorbell(camera: dict) -> bool:
    flags = _feature_flags(camera)
    return bool(flags.get('isDoorbell'))


def camera_nodedef_for(camera: dict) -> str:
    smart = camera_smart_types(camera)
    audio = camera_audio_types(camera)
    if camera_is_doorbell(camera):
        return NODEDEF_DOORBELL
    if audio & _AUDIO_SMART:
        return NODEDEF_AI_AUDIO
    if smart & _AI_SMART or camera_has_line_crossing(camera):
        return NODEDEF_AI
    if smart & _BASIC_SMART or smart:
        return NODEDEF_DETECT
    return NODEDEF_DETECT


def camera_supports_smart_type(camera: dict, normalized_type: str) -> bool:
    norm = normalize_detect_type(normalized_type)
    if norm == 'motion':
        return True
    if norm == 'line' or norm == 'linecross':
        return camera_supports_line_events(camera)
    if norm in _AUDIO_SMART:
        return norm in camera_audio_types(camera)
    if norm in _AI_SMART or norm in _BASIC_SMART:
        return norm in camera_smart_types(camera)
    return norm in camera_smart_types(camera) or norm in camera_audio_types(camera)
