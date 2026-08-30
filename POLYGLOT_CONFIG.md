# UniFi Protect — Polyglot Configuration

Configuration guide for the **UniFi Protect NodeServer** (Polyglot V3 on EISY/Polisy).

## Prerequisites

1. UniFi Protect controller (UDM Pro, UDM SE, UCK Gen2+, etc.) on your LAN
2. UniFi OS 2.0 or later
3. Either a UniFi **API key** (recommended) or a local admin account on the UniFi controller
4. Smart detection enabled on cameras you want Person/Vehicle/Animal/Package drivers for

## Configuration parameters

Enter all values in the Polyglot UI **Configuration** tab.

### Required

#### `host`

IP address or hostname of your UniFi console (the device running Protect).

- **Example:** `192.168.1.1` or `unifi.local`

#### `api_key` (recommended)

Official UniFi Protect API key. Sent as the `X-API-KEY` header on every request.

- Create under **UniFi OS → Control Plane → Integrations → API Keys**
- When set, `username` and `password` are not required

#### `username`

Local UniFi OS account username (legacy auth when `api_key` is not set).

- Create under **Settings → Admins & Users → Add Admin**
- **Protect Manager** or **View Only** role is sufficient for detection; doorbell settings need write access

#### `password`

Password for the local UniFi OS account (legacy auth when `api_key` is not set).

### Optional

#### `port`

HTTPS port for the UniFi console.

- **Default:** `443`

#### `verify_ssl`

Whether to verify the controller's SSL certificate.

- **Default:** `false`
- **Recommended:** Leave at `false` for typical self-signed LAN certificates

#### `detection_timeout`

Seconds before a stuck detection driver auto-clears if Protect's closing WebSocket event is missed.

- **Default:** `300`
- **Disable:** Set to `0`

Detection drivers (Motion, Person, Vehicle, Animal, Package) are ephemeral: they reset to off on plugin startup and clear when Protect closes the event.

#### `watchdog_minutes`

Minutes of sustained connection failure before the plugin restarts itself as a last resort.

- **Default:** `5`
- **Disable:** Set to `0`

Brief network blips are retried automatically; a Polyglot notice appears after about one minute offline.

## Camera nodes

Each Protect camera becomes an ISY node keyed by MAC address (stable across re-adoption).

### Drivers

- **Connected** — camera is online
- **Motion** — motion detected
- **Person** — person smart detection
- **Vehicle** — vehicle smart detection
- **Animal** — animal smart detection
- **Package** — package smart detection
- **Ring Volume** — doorbell speaker volume (0–100%)
- **Repeat Times** — ringtone repeat count (1–5)
- **Ringtone** — current ringtone (names loaded from Protect)

Ring Volume, Repeat Times, and Ringtone apply to cameras with speakers (doorbells).

### Commands

- **Set Ringtone** — choose ringtone from dropdown (names from Protect)
- **Set Ring Volume** — set doorbell volume
- **Set Repeat Times** — set how many times the ringtone plays
- **Query** — refresh drivers from the Protect API

## Controller commands

- **Re-Discover** — re-sync cameras and speaker settings from Protect
- **Query All** — report all controller and camera drivers

## Troubleshooting

### No cameras appear

- Confirm `host`, `username`, and `password` in Custom Parameters
- Check Polyglot logs for login or bootstrap errors
- Run **Re-Discover** from the controller node in Admin Console

### Detection drivers stuck on

- Lower `detection_timeout` for faster auto-clear, or restart the plugin
- Drivers intentionally reset on startup so stale detections do not persist

### Connection notice will not clear

- Verify the controller is reachable on the configured `host` and `port`
- Check firewall rules between EISY/Polisy and the UniFi console

### Ringtone dropdown shows "(loading...)"

- Ringtones are fetched on first successful connect and written into the profile
- Restart the plugin after Protect is online if the list was empty on first run

## Admin Console note

Close Admin Console while changing Polyglot configuration, then reopen it after discovery so new camera nodes appear.
