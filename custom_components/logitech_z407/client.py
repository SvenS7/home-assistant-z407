"""BLE client for the Logitech Z407."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    COMMAND_CHAR_UUID,
    CONFIRMATION_TO_COMMAND,
    HANDSHAKE_ACK,
    HANDSHAKE_ACK_RESPONSE,
    HANDSHAKE_CONNECTED,
    HANDSHAKE_INIT,
    HANDSHAKE_INIT_RESPONSE,
    INPUT_SOURCE_BY_COMMAND,
    RESPONSE_CHAR_UUID,
    SOURCE_STATUS,
    Z407State,
)

_LOGGER = logging.getLogger(__name__)


class Z407ClientError(HomeAssistantError):
    """Base error for Z407 BLE client failures."""


class Z407HandshakeError(Z407ClientError):
    """Raised when the device does not finish the handshake."""


@dataclass(slots=True)
class _ConnectionContext:
    client: object
    disconnect_callback: Callable[[], None]


class Z407Client:
    """Async wrapper around the Z407 BLE protocol."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        name: str | None = None,
    ) -> None:
        self.hass = hass
        self.address = address
        self.name = name or "Logitech Z407"
        self._lock = asyncio.Lock()
        self._state = Z407State()
        self._connection: _ConnectionContext | None = None
        self._response_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._connect_lock = asyncio.Lock()
        self._client_factory: Callable[..., object] | None = None

    @property
    def state(self) -> Z407State:
        """Return a snapshot of the runtime state."""

        return self._state

    @property
    def connected(self) -> bool:
        """Return whether the BLE link is considered active."""

        return self._state.connected

    def set_client_factory(self, factory: Callable[..., object]) -> None:
        """Override the client factory for tests."""

        self._client_factory = factory

    async def async_connect(self) -> None:
        """Connect to the speaker and complete the handshake."""

        async with self._connect_lock:
            if self._state.connected and self._connection is not None:
                return

            try:
                device = await self._async_get_ble_device()
                if device is None:
                    raise Z407ClientError(f"Z407 device {self.address} is not available")

                client = await self._async_establish_client(device)
                self._connection = _ConnectionContext(
                    client=client,
                    disconnect_callback=self._handle_disconnect,
                )
                self._clear_response_queue()
                await self._async_start_notifications(client)
                await self._async_handshake(client)
                self._state.connected = True
            except Exception:
                client = self._connection.client if self._connection is not None else None
                self._connection = None
                self._state.connected = False
                if client is not None:
                    disconnect = getattr(client, "disconnect", None)
                    if disconnect is not None:
                        result = disconnect()
                        if asyncio.iscoroutine(result):
                            await result
                raise

    async def async_disconnect(self) -> None:
        """Disconnect from the device if connected."""

        async with self._connect_lock:
            if self._connection is None:
                self._state.connected = False
                return

            client = self._connection.client
            self._connection = None
            self._state.connected = False
            disconnect = getattr(client, "disconnect", None)
            if disconnect is not None:
                result = disconnect()
                if asyncio.iscoroutine(result):
                    await result

    async def async_ensure_connected(self) -> None:
        """Reconnect on demand."""

        if self._state.connected and self._connection is not None:
            return
        await self.async_connect()

    async def async_send_command(self, command: bytes) -> None:
        """Write a command and wait for its confirmation."""

        async with self._lock:
            try:
                await self.async_ensure_connected()
                client = self._require_client()
                self._clear_response_queue()
                await self._async_write(client, command)
                await self._async_wait_for_confirmation(command)
            except Z407ClientError:
                self._handle_disconnect()
                raise

    async def async_set_source(self, source_command: bytes) -> None:
        """Switch the current input source."""

        await self.async_send_command(source_command)
        self._state.input_source = INPUT_SOURCE_BY_COMMAND[source_command]

    async def async_refresh(self) -> Z407State:
        """Ensure the connection exists and return the latest state."""

        await self.async_ensure_connected()
        return self._state

    async def _async_get_ble_device(self):
        from homeassistant.components import bluetooth

        return bluetooth.async_ble_device_from_address(self.hass, self.address, True)

    async def _async_establish_client(self, device):
        if self._client_factory is not None:
            return await self._async_maybe_await(self._client_factory(device))

        from bleak_retry_connector import (
            BleakClientWithServiceCache,
            establish_connection,
        )

        return await establish_connection(
            BleakClientWithServiceCache,
            device,
            self.name,
            disconnected_callback=self._handle_disconnect,
        )

    async def _async_start_notifications(self, client) -> None:
        start_notify = getattr(client, "start_notify", None)
        if start_notify is None:
            return
        await self._async_maybe_await(start_notify(RESPONSE_CHAR_UUID, self._async_handle_notification))

    async def _async_handshake(self, client) -> None:
        await self._async_write(client, HANDSHAKE_INIT)
        await self._async_expect(HANDSHAKE_INIT_RESPONSE)
        await self._async_write(client, HANDSHAKE_ACK)
        await self._async_expect(HANDSHAKE_ACK_RESPONSE)
        await self._async_expect(HANDSHAKE_CONNECTED)

    async def _async_write(self, client, data: bytes) -> None:
        write_gatt_char = getattr(client, "write_gatt_char", None)
        if write_gatt_char is None:
            raise Z407ClientError("BLE client does not support writes")

        await self._async_maybe_await(write_gatt_char(COMMAND_CHAR_UUID, data, response=True))

    async def _async_expect(self, expected: bytes) -> None:
        try:
            while True:
                payload = await asyncio.wait_for(self._response_queue.get(), timeout=15)
                if payload == expected:
                    return
                self._process_payload(payload)
        except TimeoutError as err:
            raise Z407HandshakeError(f"Timed out waiting for {expected.hex()}") from err

    async def _async_wait_for_confirmation(self, command: bytes) -> None:
        expected_commands = {
            command,
        }
        try:
            while True:
                payload = await asyncio.wait_for(self._response_queue.get(), timeout=15)
                if payload in CONFIRMATION_TO_COMMAND:
                    if CONFIRMATION_TO_COMMAND[payload] in {
                        self._command_name(command),
                        "unknown_1",
                    }:
                        return
                if payload in SOURCE_STATUS:
                    self._process_payload(payload)
                    continue
                if payload in expected_commands:
                    return
                self._process_payload(payload)
        except TimeoutError as err:
            raise Z407ClientError(f"Timed out waiting for confirmation of {command.hex()}") from err

    def _async_handle_notification(self, _sender: int, data: bytearray) -> None:
        self._response_queue.put_nowait(bytes(data))
        self._process_payload(bytes(data))

    def _process_payload(self, payload: bytes) -> None:
        if payload in SOURCE_STATUS:
            self._state.input_source = SOURCE_STATUS[payload]

    def _clear_response_queue(self) -> None:
        while not self._response_queue.empty():
            try:
                self._response_queue.get_nowait()
            except asyncio.QueueEmpty:
                return

    def _require_client(self):
        if self._connection is None:
            raise Z407ClientError("BLE client is not connected")
        return self._connection.client

    def _handle_disconnect(self, *_args) -> None:
        _LOGGER.debug("Z407 disconnected")
        self._state.connected = False
        self._connection = None

    @staticmethod
    def _command_name(command: bytes) -> str | None:
        for name, value in {
            "bass_up": b"\x80\x00",
            "bass_down": b"\x80\x01",
            "volume_up": b"\x80\x02",
            "volume_down": b"\x80\x03",
            "media_play_pause": b"\x80\x04",
            "media_next_track": b"\x80\x05",
            "media_previous_track": b"\x80\x06",
            "pairing": b"\x82\x00",
            "factory_reset": b"\x83\x00",
            "sound_1": b"\x85\x01",
            "sound_2": b"\x85\x02",
            "sound_3": b"\x85\x03",
            "unknown_1": b"\x85\x00",
            "bluetooth": b"\x81\x01",
            "aux": b"\x81\x02",
            "usb": b"\x81\x03",
        }.items():
            if value == command:
                return name
        return None

    @staticmethod
    async def _async_maybe_await(value):
        if asyncio.iscoroutine(value):
            return await value
        return value
