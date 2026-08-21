"""UniFi Protect binary WebSocket protocol parser."""

import json
import struct
import zlib

import udi_interface

LOGGER = udi_interface.LOGGER

# Each WS message: [8-byte header][action payload][8-byte header][data payload]
# Header: uint16 packet_type, uint8 payload_format, uint8 deflate, uint32 size
# payload_format: 1=JSON, 2=UTF8, 3=binary

_HEADER_FMT = '>BBBBI'
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)

_FMT_JSON = 1
_FMT_UTF8 = 2


def _decode(data: bytes, deflate: bool, fmt: int):
    if deflate:
        data = zlib.decompress(data)
    if fmt in (_FMT_JSON, _FMT_UTF8):
        return json.loads(data)
    return data


def parse_ws_message(raw: bytes):
    """Return (action_dict, data_dict) or (None, None) on parse error."""
    try:
        if len(raw) < _HEADER_SIZE * 2:
            return None, None

        _, a_fmt, a_deflate, _, a_size = struct.unpack_from(_HEADER_FMT, raw, 0)
        a_payload = _decode(raw[_HEADER_SIZE: _HEADER_SIZE + a_size],
                            bool(a_deflate), a_fmt)

        d_off = _HEADER_SIZE + a_size
        _, d_fmt, d_deflate, _, d_size = struct.unpack_from(_HEADER_FMT, raw, d_off)
        d_payload = _decode(raw[d_off + _HEADER_SIZE: d_off + _HEADER_SIZE + d_size],
                            bool(d_deflate), d_fmt)

        return a_payload, d_payload
    except Exception as e:
        LOGGER.debug(f'WS parse error: {e}')
        return None, None
