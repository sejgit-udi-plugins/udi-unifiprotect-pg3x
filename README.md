# UniFi Protect PG3x NodeServer

NodeServer for Universal Devices **EISY** or **Polisy** (Polyglot V3) that integrates UniFi Protect cameras with the ISY/IoX home automation controller. Each camera appears as a node with real-time motion and smart detection drivers.

Repository: [sejgit-udi-plugins/udi-unifiprotect-pg3x](https://github.com/sejgit-udi-plugins/udi-unifiprotect-pg3x)

## Features

- Real-time motion and smart detection via Public Integration API WebSockets
- Per-camera drivers: Connected, Motion, Person, Vehicle, Animal, Package
- USL / UP Sense sensor support: contact, leak, motion, tamper, alarm, glass break, temp, humidity, light
- API-key-only auth (UniFi Protect 5.3+ Integration API)
- Local API only — no Ubiquiti cloud required
- aiohttp-only client (FreeBSD / EISY compatible)

## Requirements

- UniFi Protect controller (UDM Pro, UDM SE, UCK Gen2+, etc.)
- UniFi OS 2.0+ with Protect **5.3+**
- Integration API key from **Control Plane → Integrations**

## Installation

Add the NodeServer in PG3x:

- **GitHub URL:** `https://github.com/sejgit-udi-plugins/udi-unifiprotect-pg3x`
- **Executable:** `udi-unifiprotect-pg3x.py`

See [POLYGLOT_CONFIG.md](POLYGLOT_CONFIG.md) for configuration details.

## Development

```bash
make install    # uv sync --dev
make test       # pytest (profile + version sync)
make lint       # ruff
make fulltest   # pre-commit on all files
```

Version bumps: edit `VERSION` in `udi-unifiprotect-pg3x.py`, update `CHANGELOG.md`, then `make sync-version`.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the full release workflow.

## License

MIT — see [LICENSE](LICENSE)
