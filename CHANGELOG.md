# Changelog

All notable changes to this project are documented here.

## 1.3.0

- Add USL / UP Sense sensor nodes via `GET /integration/v1/sensors`
- Per-sensor drivers: motion, contact, leak, tamper, alarm, glass break, temp, humidity, light
- Capability-aware driver mapping from Protect `featureFlags`

## 1.2.0

- Migrate to UniFi Protect Public Integration API (v1) with API-key-only auth
- Camera discovery via `GET /integration/v1/cameras`
- Live updates via `subscribe/events` and `subscribe/devices` WebSockets
- Remove legacy private bootstrap API and username/password configuration
- Drop doorbell ringtone/volume commands until official API support is added

## 1.1.0

- Real-time WebSocket motion and smart detection drivers
- Doorbell ringtone, volume, and repeat control
- Standard PG3x bootstrap, server.json, and version sync tooling
