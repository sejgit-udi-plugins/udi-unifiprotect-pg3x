# Changelog

All notable changes to this project are documented here.

## 1.5.2

- Complete NLS command names for all nodedefs (fixes missing Control triggers on AI+Audio cameras)
- Add CONNECTED/DISCONNECTED control commands for online/offline transitions
- Add profile test ensuring every send command has an ISY program label

## 1.5.1

- Fix line crossing ignored on public API cameras (``hasLineCrossing`` omitted from featureFlags)
- Log line crossing events at INFO for easier EISY troubleshooting

## 1.5.0

- Capability-based camera nodedefs: detect, AI (face/LPR/line), AI+audio, doorbell
- Expand camera events: line crossing, audio detections (smoke, CO, siren, etc.), doorbell ring
- Capability-based sensor nodedefs: contact, motion, leak, glass, environmental — no unused drivers at 0
- Add `temperature_units` config (C or F; default F) for UP Sense environmental sensors
- Detection and sensor state changes emit ISY control commands (`reportCmd`) for program triggers
- Document Public API scope, read-only design, and Global Alarm Manager alignment in README

## 1.3.2

- Fix sensor live updates dropped after partial WebSocket messages recalculated capabilities
- Only refresh sensor capability map when config fields change; infer modelKey from device id
- Apply driver updates only for fields present in each WebSocket payload

## 1.3.1

- Fix sensor Connected flapping on WebSocket partial updates (merge cached state)
- Fix environmental UOMs: °C=4, lux=36 (was inches/wind direction)

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
