# UniFi Mobility for Home Assistant

A local Home Assistant integration for Ubiquiti UniFi Mobile Router devices, including UMR, UMR-Industrial, and compatible UMR variants.

It communicates directly with the **UMR Local Portal JSON-RPC API**. No Mobility Cloud subscription is required, and router telemetry stays on your local network.

> This is an independent community project and is not affiliated with or endorsed by Ubiquiti Inc.

## Features

- Local polling with automatic session renewal
- Home Assistant reauthentication when the local portal password changes
- Separate fast and slow polling to reduce router load
- Chinese and English user interfaces
- Local brand assets for Home Assistant 2026.3+
- Redacted diagnostics with credentials and device identifiers removed
- HACS-compatible repository structure

## Available entities

### Connectivity and cellular

- Internet connectivity
- Activation state
- SIM presence and PIN lock state
- Operator, network source, LTE band, and cellular network type
- RSSI, RSRP, RSRQ, and calculated signal quality
- RX and TX channels

### Device and network

- Firmware version
- CPU and memory utilization
- Uptime
- WAN/LAN IPv4 and WAN IPv6
- Connected client count
- LTE modem model
- PoE passthrough state

### Data plan

- Current data usage
- Configured data limit
- Billing-cycle value

IMEI and ICCID entities are disabled by default because they are sensitive identifiers.

## Requirements

- Home Assistant 2026.3 or newer is recommended
- A supported UniFi Mobile Router reachable from Home Assistant
- The password used by the router's local portal
- Stable UMR firmware; tested with UMR-Industrial-EU firmware `1.17.11`

## Installation

### HACS

1. Open HACS.
2. Add this repository as a custom repository with category **Integration**.
3. Install **UniFi Mobility**.
4. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/unifi_mobility` into Home Assistant's `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **UniFi Mobility**.

## Configuration

For a typical UMR installation:

| Field | Example | Notes |
|---|---|---|
| Host | `192.168.105.1` | Scheme is optional; HTTPS is used by default |
| Password | Local portal password | The local username is fixed to `ui` |
| Verify SSL | Off | UMR devices normally use a self-signed certificate |

After setup, open the integration's **Configure** dialog to change:

- Host address and password
- SSL certificate verification
- Fast polling interval (15–300 seconds)
- Slow polling multiplier
- Client-list polling

The default schedule polls live signal and status every 30 seconds, while static information and the client list are refreshed every 5 minutes.

## Signal quality

Signal quality is calculated primarily from RSRP:

| RSRP | Rating |
|---|---|
| Above −80 dBm | Excellent |
| −80 to −90 dBm | Good |
| −90 to −100 dBm | Fair |
| Below −100 dBm | Poor |

## Privacy and security

- Communication is local between Home Assistant and the router.
- The integration performs read-only status calls.
- Passwords are stored in Home Assistant's config-entry storage.
- Diagnostics redact passwords, session tokens, addresses, MAC addresses, IMEI, ICCID, SSIDs, and client identifiers.
- No analytics or external telemetry is included.

## Troubleshooting

### Cannot connect

- Confirm Home Assistant can reach the UMR address.
- Open the local portal in a browser and verify the password.
- Keep SSL verification disabled unless the router has a trusted certificate.

### Entities are unavailable

UMR firmware versions expose slightly different JSON-RPC methods. Unsupported optional sections are kept unavailable without breaking the whole integration.

### Password changed

Home Assistant will create a repair/reauthentication flow. Enter the new local portal password without deleting the integration.

## Development

```bash
uvx ruff format custom_components tests
uvx ruff check custom_components tests
python3 -m compileall -q custom_components/unifi_mobility
```

The repository includes GitHub Actions workflows for Ruff, Hassfest, and HACS validation.

## License

MIT. Ubiquiti, UniFi, and related marks are trademarks of Ubiquiti Inc.
