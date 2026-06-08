"""Buttons for Logitech Z407."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Z407ClientError
from .const import BASS_STEPS, BUTTON_COMMANDS, DOMAIN, build_device_info
from .coordinator import Z407Coordinator


@dataclass(slots=True)
class ButtonDefinition:
    key: str
    translation_key: str
    name: str
    enabled_default: bool = True


BUTTONS = [
    ButtonDefinition("bass_calibrate", "bass_calibrate", "Calibrate Bass"),
    ButtonDefinition("pairing", "pairing", "Bluetooth Pairing Mode"),
    ButtonDefinition("sound_1", "sound_1", "Sound Mode 1"),
    ButtonDefinition("sound_2", "sound_2", "Sound Mode 2"),
    ButtonDefinition("sound_3", "sound_3", "Sound Mode 3"),
    ButtonDefinition("factory_reset", "factory_reset", "Factory Reset", False),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button entities."""

    coordinator: Z407Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            LogitechZ407Button(coordinator, button)
            for button in BUTTONS
        ]
    )


class LogitechZ407Button(CoordinatorEntity[Z407Coordinator], ButtonEntity):
    """A Z407 command button."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Z407Coordinator, button: ButtonDefinition) -> None:
        super().__init__(coordinator)
        self._client = coordinator.client
        self._button = button
        self._attr_translation_key = button.translation_key
        self._attr_unique_id = f"{self._client.address}-button-{button.key}"
        self._attr_entity_registry_enabled_default = button.enabled_default
        self._attr_name = button.name

    @property
    def device_info(self):
        return build_device_info(self._client.address)

    @property
    def available(self) -> bool:
        return self.coordinator.data.connected if self.coordinator.data else False

    async def async_press(self) -> None:
        if not self.available:
            raise Z407ClientError(
                f"Cannot press {self._button.name}: "
                f"Logitech Z407 ({self._client.address}) is not connected. "
                "Make sure the speaker is powered on and Bluetooth is available."
            )
        try:
            if self._button.key == "bass_calibrate":
                for _ in range(BASS_STEPS):
                    await self._client.async_send_command(
                        BUTTON_COMMANDS["bass_down"]
                    )
                self._client.state.bass_level = 0
            else:
                await self._client.async_send_command(
                    BUTTON_COMMANDS[self._button.key]
                )
            await self.coordinator.async_request_refresh()
        except Z407ClientError:
            raise
