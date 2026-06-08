# Logitech Z407 for Home Assistant

Custom HACS integration for the Logitech Z407 Bluetooth speaker system.

## What it does

- Discovers connectable Z407 speakers over Bluetooth using service UUID `0000fdc2-0000-1000-8000-00805f9b34fb`.
- Creates a UI config flow in Home Assistant.
- Exposes a `media_player` entity for playback-oriented commands.
- Exposes an input source `select` for Bluetooth, AUX, and USB.
- Exposes buttons for bass, pairing, sound cues, and factory reset.
- Handles BLE reconnects and command serialization inside Home Assistant.

## Supported features

- Media player controls:
  - play/pause
  - next track
  - previous track
  - volume up
  - volume down
- Input select:
  - Bluetooth
  - AUX
  - USB
- Buttons:
  - Bass Up
  - Bass Down
  - Bluetooth Pairing Mode
  - Sound 1
  - Sound 2
  - Sound 3
  - Factory Reset

## Installation

### Via HACS

1. Add this repository as a custom repository in HACS and choose the `Integration` category.
2. Install the integration.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration** and wait for Bluetooth discovery.

### Manual

1. Copy `custom_components/logitech_z407` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from the UI after Bluetooth discovery.

## Development

Use `uv` for the local workflow:

- `uv sync --extra dev`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest`

## Troubleshooting

- If the speaker does not advertise, make sure the original Logitech remote is not connected.
- The Z407 only allows one active Bluetooth control connection at a time.
- If pairing fails, power-cycle the speaker and make sure Bluetooth is available in Home Assistant.

## Protocol source

This integration is based on the reverse-engineering notes in [freundTech/logi-z407-reverse-engineering](https://github.com/freundTech/logi-z407-reverse-engineering).

That source does not provide a license, so protocol usage here is at your own risk.

This is not an official Logitech integration and is not supported by Logitech.

## License

The code in this repository is MIT licensed.
