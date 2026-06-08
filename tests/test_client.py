"""Tests for the Z407 BLE client."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from custom_components.logitech_z407.client import Z407Client
from custom_components.logitech_z407.const import (
    BUTTON_COMMANDS,
    COMMAND_CHAR_UUID,
    HANDSHAKE_ACK,
    HANDSHAKE_ACK_RESPONSE,
    HANDSHAKE_CONNECTED,
    HANDSHAKE_INIT,
    HANDSHAKE_INIT_RESPONSE,
    MEDIA_COMMANDS,
    RESPONSE_CHAR_UUID,
    SOURCE_COMMANDS,
    SOURCE_STATUS,
)

COMMAND_CONFIRMATIONS = {
    BUTTON_COMMANDS["bass_up"]: b"\xc0\x00",
    BUTTON_COMMANDS["bass_down"]: b"\xc0\x01",
    BUTTON_COMMANDS["volume_up"]: b"\xc0\x02",
    BUTTON_COMMANDS["volume_down"]: b"\xc0\x03",
    MEDIA_COMMANDS["media_play_pause"]: b"\xc0\x04",
    MEDIA_COMMANDS["media_next_track"]: b"\xc0\x05",
    MEDIA_COMMANDS["media_previous_track"]: b"\xc0\x06",
    SOURCE_COMMANDS["bluetooth"]: (b"\xc1\x01", SOURCE_STATUS[b"\xcf\x04"]),
    SOURCE_COMMANDS["aux"]: (b"\xc1\x02", SOURCE_STATUS[b"\xcf\x05"]),
    SOURCE_COMMANDS["usb"]: (b"\xc1\x03", SOURCE_STATUS[b"\xcf\x06"]),
    BUTTON_COMMANDS["pairing"]: b"\xc2\x00",
    BUTTON_COMMANDS["factory_reset"]: b"\xc3\x00",
    BUTTON_COMMANDS["sound_1"]: b"\xc5\x03",
    BUTTON_COMMANDS["sound_2"]: b"\xc5\x02",
    BUTTON_COMMANDS["sound_3"]: b"\xc5\x01",
}


@dataclass
class FakeBleDevice:
    address: str
    name: str = "Logitech Z407"


class FakeBleClient:
    def __init__(self):
        self.writes = []
        self.started = []
        self.callback = None

    async def start_notify(self, char_uuid, callback):
        self.started.append(char_uuid)
        self.callback = callback

    async def write_gatt_char(self, char_uuid, data, response=True):
        self.writes.append((char_uuid, bytes(data), response))
        if self.callback is None:
            return
        payload = COMMAND_CONFIRMATIONS.get(bytes(data))
        if bytes(data) == HANDSHAKE_INIT:
            payload = HANDSHAKE_INIT_RESPONSE
        elif bytes(data) == HANDSHAKE_ACK:
            self.callback(1, bytearray(HANDSHAKE_ACK_RESPONSE))
            self.callback(1, bytearray(HANDSHAKE_CONNECTED))
            return
        if isinstance(payload, tuple):
            confirmation, status = payload
            self.callback(1, bytearray(confirmation))
            self.callback(1, bytearray(status))
            return
        if payload is not None:
            self.callback(1, bytearray(payload))

    async def disconnect(self):
        return None


@pytest.fixture
def client(hass):
    z407 = Z407Client(hass, "AA:BB:CC:DD:EE:FF")
    fake = FakeBleClient()
    z407.set_client_factory(lambda _device: fake)
    return z407, fake


@pytest.mark.asyncio
async def test_handshake_sequence(client, monkeypatch):
    z407, fake = client

    async def fake_get_device():
        return FakeBleDevice(address=z407.address)

    monkeypatch.setattr(z407, "_async_get_ble_device", fake_get_device)
    await z407.async_connect()

    assert fake.started == [RESPONSE_CHAR_UUID]
    assert fake.writes[0][1] == HANDSHAKE_INIT
    assert fake.writes[1][1] == HANDSHAKE_ACK
    assert z407.connected is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,command,expected_confirmation,expected_source",
    [
        ("async_send_command", BUTTON_COMMANDS["bass_up"], b"\xc0\x00", None),
        ("async_send_command", BUTTON_COMMANDS["bass_down"], b"\xc0\x01", None),
        ("async_send_command", BUTTON_COMMANDS["volume_up"], b"\xc0\x02", None),
        ("async_send_command", BUTTON_COMMANDS["volume_down"], b"\xc0\x03", None),
        ("async_send_command", MEDIA_COMMANDS["media_play_pause"], b"\xc0\x04", None),
        ("async_send_command", MEDIA_COMMANDS["media_next_track"], b"\xc0\x05", None),
        ("async_send_command", MEDIA_COMMANDS["media_previous_track"], b"\xc0\x06", None),  # noqa: E501
        ("async_set_source", SOURCE_COMMANDS["bluetooth"], b"\xc1\x01", "bluetooth"),
        ("async_set_source", SOURCE_COMMANDS["aux"], b"\xc1\x02", "aux"),
        ("async_set_source", SOURCE_COMMANDS["usb"], b"\xc1\x03", "usb"),
        ("async_send_command", BUTTON_COMMANDS["pairing"], b"\xc2\x00", None),
        ("async_send_command", BUTTON_COMMANDS["factory_reset"], b"\xc3\x00", None),
        ("async_send_command", BUTTON_COMMANDS["sound_1"], b"\xc5\x03", None),
        ("async_send_command", BUTTON_COMMANDS["sound_2"], b"\xc5\x02", None),
        ("async_send_command", BUTTON_COMMANDS["sound_3"], b"\xc5\x01", None),
    ],
)
async def test_command_writes_exact_bytes(
    client,
    monkeypatch,
    method,
    command,
    _expected_confirmation,
    expected_source,
):
    z407, fake = client

    async def fake_get_device():
        return FakeBleDevice(address=z407.address)

    monkeypatch.setattr(z407, "_async_get_ble_device", fake_get_device)
    await z407.async_connect()
    await getattr(z407, method)(command)
    assert fake.writes[-1] == (COMMAND_CHAR_UUID, command, True)
    if expected_source is not None:
        assert z407.state.input_source == expected_source


@pytest.mark.asyncio
async def test_status_decoder_updates_input_source(client):
    z407, _fake = client

    z407._process_payload(SOURCE_STATUS[b"\xcf\x04"])
    assert z407.state.input_source == "bluetooth"
