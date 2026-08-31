# Unifi Protect api

NodeServer for Universal Devices **EISY** or **Polisy** (Polyglot V3). UniFi Protect api integration of cameras and USL/UP Sense sensors — detection events for ISY programs.

**UD store listing:** `UnifiProtapi` (15-character name limit on the store; same plugin as this repo).

Repository: [sejgit-udi-plugins/udi-unifiprotectapi-pg3x](https://github.com/sejgit-udi-plugins/udi-unifiprotectapi-pg3x)

## Scope and design

This plugin is built exclusively on Ubiquiti's **Public Integration API** (API-key auth, no username/password). As that API grows, this plugin will grow with it — new endpoints and event types will be adopted when they are officially documented and stable.

**Read-only for now.** The plugin subscribes to Protect (cameras, sensors, events) and reports state into ISY. It does not send commands back to UniFi (no arming, recording, doorbell settings, etc.).

**Global Alarm Manager alignment.** Features are limited to what is available when Protect is configured with **Global Alarm Manager** rather than local-only alarms. Camera and sensor event subscriptions cover the integration surface needed for ISY programs; full Alarm Manager arm/disarm API is deferred until it is exposed on the public API.

**ISY program triggers.** Detection and state changes emit ISY **control commands** (e.g. `MOTION`, `OPEN`, `PERSON`) in addition to driver updates, so programs can trigger on events — not only on the Connected driver.

## Features

- Real-time motion and smart detection via Public Integration API WebSockets
- Capability-based camera nodedefs: basic detect, AI (face, LPR, line crossing), AI+audio, doorbell
- Capability-based sensor nodedefs: contact, motion, leak, glass break, environmental (UP Sense)
- Configurable temperature units (°C or °F) for environmental sensors
- USL / UP Sense sensor support via `GET /integration/v1/sensors`
- API-key-only auth (UniFi Protect 5.3+ Integration API)
- Local API only — no Ubiquiti cloud required
- aiohttp-only client (FreeBSD / EISY compatible)

## Requirements

- UniFi Protect controller (UDM Pro, UDM SE, UCK Gen2+, etc.)
- UniFi OS 2.0+ with Protect **5.3+**
- Integration API key from **Control Plane → Integrations**

## Installation

Add the NodeServer in PG3x:

- **GitHub URL:** `https://github.com/sejgit-udi-plugins/udi-unifiprotectapi-pg3x`
- **Executable:** `udi-unifiprotectapi-pg3x.py`

After upgrading to v1.5+, reinstall the NodeServer profile on EISY so new capability-based nodedefs are loaded, then run **Re-Discover**.

See [POLYGLOT_CONFIG.md](POLYGLOT_CONFIG.md) for configuration details.

## Development

```bash
make install    # uv sync --dev
make test       # pytest (profile + version sync)
make lint       # ruff
make fulltest   # pre-commit on all files
```

Version bumps: edit `VERSION` in `udi-unifiprotectapi-pg3x.py`, update `CHANGELOG.md`, then `make sync-version`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the full release workflow.

## License

MIT — see [LICENSE](LICENSE)
