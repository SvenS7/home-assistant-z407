"""Constants for Logitech Z407."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo

DOMAIN = "logitech_z407"
MANUFACTURER = "Logitech"
MODEL = "Z407"

CONF_ADDRESS = "address"

SERVICE_UUID = "0000fdc2-0000-1000-8000-00805f9b34fb"
RESPONSE_CHAR_UUID = "b84ac9c6-29c5-46d4-bba1-9d534784330f"
COMMAND_CHAR_UUID = "c2e758b9-0e78-41e0-b0cb-98a593193fc5"

HANDSHAKE_INIT = b"\x84\x05"
HANDSHAKE_ACK = b"\x84\x00"
HANDSHAKE_INIT_RESPONSE = b"\xd4\x05\x01"
HANDSHAKE_ACK_RESPONSE = b"\xd4\x00\x01"
HANDSHAKE_CONNECTED = b"\xd4\x00\x03"

SOURCE_BLUETOOTH = "bluetooth"
SOURCE_AUX = "aux"
SOURCE_USB = "usb"

SOURCE_OPTIONS = [SOURCE_BLUETOOTH, SOURCE_AUX, SOURCE_USB]
SOURCE_LABELS = {
    SOURCE_BLUETOOTH: "Bluetooth",
    SOURCE_AUX: "AUX",
    SOURCE_USB: "USB",
}

SOURCE_COMMANDS = {
    SOURCE_BLUETOOTH: b"\x81\x01",
    SOURCE_AUX: b"\x81\x02",
    SOURCE_USB: b"\x81\x03",
}

BUTTON_COMMANDS = {
    "bass_up": b"\x80\x00",
    "bass_down": b"\x80\x01",
    "pairing": b"\x82\x00",
    "sound_1": b"\x85\x01",
    "sound_2": b"\x85\x02",
    "sound_3": b"\x85\x03",
    "factory_reset": b"\x83\x00",
}

MEDIA_COMMANDS = {
    "media_play_pause": b"\x80\x04",
    "media_next_track": b"\x80\x05",
    "media_previous_track": b"\x80\x06",
    "volume_up": b"\x80\x02",
    "volume_down": b"\x80\x03",
}

CONFIRMATION_TO_COMMAND = {
    b"\xc0\x00": "bass_up",
    b"\xc0\x01": "bass_down",
    b"\xc0\x02": "volume_up",
    b"\xc0\x03": "volume_down",
    b"\xc0\x04": "media_play_pause",
    b"\xc0\x05": "media_next_track",
    b"\xc0\x06": "media_previous_track",
    b"\xc1\x01": SOURCE_BLUETOOTH,
    b"\xc1\x02": SOURCE_AUX,
    b"\xc1\x03": SOURCE_USB,
    b"\xc2\x00": "pairing",
    b"\xc3\x00": "factory_reset",
    b"\xc5\x03": "sound_1",
    b"\xc5\x02": "sound_2",
    b"\xc5\x01": "sound_3",
    b"\xc5\x00": "unknown_1",
}

SOURCE_STATUS = {
    b"\xcf\x04": SOURCE_BLUETOOTH,
    b"\xcf\x05": SOURCE_AUX,
    b"\xcf\x06": SOURCE_USB,
}

INPUT_SOURCE_BY_COMMAND = {
    SOURCE_COMMANDS[SOURCE_BLUETOOTH]: SOURCE_BLUETOOTH,
    SOURCE_COMMANDS[SOURCE_AUX]: SOURCE_AUX,
    SOURCE_COMMANDS[SOURCE_USB]: SOURCE_USB,
}

MEDIA_FEATURES = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
)


@dataclass(slots=True)
class Z407State:
    """Runtime state snapshot."""

    connected: bool = False
    input_source: str | None = None


def build_device_info(address: str) -> DeviceInfo:
    """Build a Home Assistant device record."""

    return DeviceInfo(
        identifiers={(DOMAIN, address)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        connections={(CONNECTION_BLUETOOTH, address)},
        name="Logitech Z407",
    )
