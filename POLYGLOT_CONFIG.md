# UniFi Protect — Polyglot Configuration

Configuration guide for the **UniFi Protect NodeServer** (Polyglot V3 on EISY/Polisy).

## Prerequisites

1. UniFi Protect controller (UDM Pro, UDM SE, UCK Gen2+, etc.) on your LAN
2. UniFi OS 2.0 or later with Protect **5.3+** (Public Integration API)
3. A UniFi **API key** created under **Control Plane → Integrations**
4. Smart detection enabled on cameras you want Person/Vehicle/Animal/Package drivers for

## Authentication

This plugin uses Ubiquiti's **Public Integration API** (`/proxy/protect/integration/v1/...`) with an **API key only**. No username or password is stored.

Create the key in the UniFi console:

**UniFi OS → Control Plane → Integrations → API Keys**

API key scoping on UniFi's side is still evolving; use a dedicated integration key rather than a personal admin key when possible.

## Configuration parameters

Enter all values in the Polyglot UI **Configuration** tab.

### Required

#### `host`

IP address or hostname of your UniFi console (the device running Protect).

- **Example:** `192.168.1.1` or `unifi.local`

#### `api_key`

Official UniFi Protect Integration API key.

- Sent as the `X-API-KEY` header on REST and WebSocket requests
- Required — the plugin does not use legacy username/password login

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

#### `temperature_units`

Display unit for environmental sensor temperature (UP Sense).

- **Default:** `F` (Fahrenheit, ISY uom 17)
- **Alternative:** `C` (Celsius, ISY uom 4)

Protect always reports temperature in Celsius; the plugin converts for display when `F` is selected.

## Sensor nodes (USL Gateway / UP Sense)

Each adopted Protect sensor becomes an ISY node keyed by MAC address. The plugin picks a **capability-based nodedef** so only relevant drivers appear (no unused slots stuck at 0).

| Nodedef | Typical hardware |
|---|---|
| **Contact** | USL Entry, UP Sense door/window |
| **Motion** | Standalone PIR |
| **Leak** | Leak sensor |
| **Glass Break** | USL Glass Break |
| **Environmental** | UP Sense multi-sensor (temp, humidity, light, contact, leak, etc.) |

Drivers are mapped from the sensor **capability map** (`featureFlags`) when Protect provides it; older firmware falls back to mount type and settings.

### Binary drivers and ISY control commands

State and detection changes emit ISY **control commands** (e.g. `OPEN`, `MOTION`, `LEAK`) so programs can trigger on events — not only on driver status.

| Capability | Control commands (ON / OFF) |
|---|---|
| Contact open | `OPEN` / `CLOSED` |
| Motion | `MOTION` / `NOMOTION` |
| Leak | `LEAK` / `NOLEAK` |
| Tamper | `TAMPER` / `NOTAMPER` |
| Alarm (smoke/CO sound) | `ALARM` / `NOALARM` |
| Glass break | `GLASS` / `NOGLASS` |

Ephemeral detections (motion from events, glass break) auto-clear after `detection_timeout` if Protect does not send a close event.

### Numeric drivers (environmental nodedef only)

| Driver | Meaning | Units |
|---|---|---|
| **Temperature** | `stats.temperature` | °C or °F per `temperature_units` |
| **Humidity** | `stats.humidity` | % (ISY uom 22) |
| **Light Level** | `stats.light` | lux (ISY uom 36) |

### Commands

- **Query** — refresh all drivers from the Protect API

## Camera nodes

Each Protect camera becomes an ISY node keyed by MAC address (stable across re-adoption). The plugin selects a nodedef from camera **feature flags**:

| Nodedef | Includes |
|---|---|
| **Detect** | Motion, Person, Vehicle, Animal, Package |
| **AI** | Above + Face, License Plate (detection only), Line Crossing |
| **AI + Audio** | Above + smoke, CO, siren, baby cry, horn, glass, speak, bark, car alarm |
| **Doorbell** | Motion, smart detect, Face, Ring |

### ISY control commands

Detection drivers emit paired control commands (e.g. `PERSON` / `NOPERSON`, `RING` / `NORING`) on transitions. Programs should use **Control** triggers on these commands.

Supported event types from the public API include `motion`, `smartDetectZone`, `smartDetectLine`, `smartAudioDetect`, and `ring`. Rich metadata (recognized face name, plate text) is not available on the public events stream.

### Commands

- **Query** — refresh connected status from the Protect API

Doorbell ringtone/volume and Alarm Manager arm/disarm are **not** implemented (read-only plugin; deferred until public API support).

## Scope

- **Public Integration API only** — grows as Ubiquiti expands the official API
- **Read-only** — subscribes to Protect; does not write commands to UniFi
- **Global Alarm Manager** — features align with Global (not local-only) alarm configuration

## Controller commands

- **Re-Discover** — re-sync cameras from Protect
- **Query All** — report all controller and camera drivers

## Troubleshooting

### No cameras appear

- Confirm `host` and `api_key` in Custom Parameters
- Verify Protect 5.3+ and that the API key is active under Integrations
- Check Polyglot logs for HTTP 401/403 (invalid or revoked key)
- Run **Re-Discover** from the controller node in Admin Console

### Detection drivers stuck on

- Lower `detection_timeout` for faster auto-clear, or restart the plugin
- Drivers intentionally reset on startup so stale detections do not persist

### Connection notice will not clear

- Verify the controller is reachable on the configured `host` and `port`
- Check firewall rules between EISY/Polisy and the UniFi console

## Admin Console note

Close Admin Console while changing Polyglot configuration, then reopen it after discovery so new camera nodes appear.
