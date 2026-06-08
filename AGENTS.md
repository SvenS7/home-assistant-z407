# AGENTS.md — Logitech Z407 (Home Assistant)

## Dev loop (uv)

```powershell
uv sync --extra dev
uv run ruff check .
uv run pyright
uv run pytest
uv run pytest tests/test_client.py::test_handshake_sequence  # single test
```

Run lint → typecheck → test in that order. Must be Python 3.13+.

## Architecture

Single HACS integration at `custom_components/logitech_z407/`. Three platforms: `media_player`, `select` (input source), `button` (7 buttons — factory_reset disabled by default). BLE handshake: INIT → ACK → CONNECTED. All commands written to `COMMAND_CHAR_UUID`, confirmations read from `RESPONSE_CHAR_UUID`. Coordinator refreshes every 60s.

## Testing quirks

- Uses `pytest-homeassistant-custom-component` — `hass` fixture injected automatically
- Config flow has a class-level `discovered_devices` dict; `conftest.py` resets it between tests (autouse fixture)
- Tests use `FakeBleClient` + `monkeypatch` — no BLE hardware needed
- `asyncio_mode = auto` in pyproject.toml (no need for `@pytest.mark.asyncio` on async fixtures, but tests use it explicitly)

## Notable

- Uses `bleak-retry-connector` for BLE, not raw `bleak`
- BLE service UUID: `0000fdc2-0000-1000-8000-00805f9b34fb` (matches Z407 remote protocol)
- No CI workflow or pre-commit hooks configured
