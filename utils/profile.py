"""Dynamic profile writer for ringtone dropdowns."""

import os

import udi_interface

LOGGER = udi_interface.LOGGER

_STATIC_NLS = """\
# Node Server Names
ND-unifi_controller-NAME = UniFi Protect Controller
ND-unifi_camera-NAME = UniFi Camera

# Controller Drivers
ST-unifi_controller-ST-NAME = Status

# Controller Commands
CMD-unifi_controller-DISCOVER-NAME = Re-Discover
CMD-unifi_controller-QUERY-NAME = Query All

# Camera Drivers
ST-unifi_camera-ST-NAME = Connected
ST-unifi_camera-GV1-NAME = Motion
ST-unifi_camera-GV2-NAME = Person
ST-unifi_camera-GV3-NAME = Vehicle
ST-unifi_camera-GV4-NAME = Animal
ST-unifi_camera-GV5-NAME = Package
ST-unifi_camera-GV6-NAME = Ring Volume
ST-unifi_camera-GV7-NAME = Repeat Times
ST-unifi_camera-GV8-NAME = Ringtone

# Camera Commands
CMD-unifi_camera-QUERY-NAME = Query
CMD-unifi_camera-SET_RINGTONE-NAME = Set Ringtone
CMD-unifi_camera-SET_RING_VOL-NAME = Set Ring Volume
CMD-unifi_camera-SET_REPEAT-NAME = Set Repeat Times

"""


def write_profile(profile_dir: str, ringtones: list):
    """Write NLS and editors with dynamic ringtone list."""
    names = [r.get('name', f'Ringtone {i}') for i, r in enumerate(ringtones)]

    nls = _STATIC_NLS
    nls += '\n# Dynamic — Ringtones\n'
    for i, name in enumerate(names):
        nls += f'RINGTONE-{i} = {name}\n'
    if not names:
        nls += 'RINGTONE-0 = (none)\n'
    with open(os.path.join(profile_dir, 'nls', 'en_us.txt'), 'w') as f:
        f.write(nls)

    subset = ','.join(str(i) for i in range(len(names))) if names else '0'
    editors = f"""<editors>
  <editor id="E_STATUS">
    <range uom="2" subset="0,1"/>
  </editor>
  <editor id="E_VOL">
    <range uom="51" min="0" max="100" prec="0"/>
  </editor>
  <editor id="E_REPEAT">
    <range uom="56" min="1" max="5" step="1"/>
  </editor>
  <editor id="E_RINGTONE">
    <range uom="25" subset="{subset}" nls="RINGTONE"/>
  </editor>
</editors>
"""
    with open(os.path.join(profile_dir, 'editor', 'editors.xml'), 'w') as f:
        f.write(editors)

    LOGGER.info(f'Profile updated: {len(names)} ringtone(s)')
