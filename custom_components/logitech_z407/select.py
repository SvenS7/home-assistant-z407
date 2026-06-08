"""Input source select for Logitech Z407."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Z407ClientError
from .const import (
    DOMAIN,
    SOURCE_COMMANDS,
    SOURCE_LABELS,
    SOURCE_OPTIONS,
    build_device_info,
)
from .coordinator import Z407Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select entity."""

    coordinator: Z407Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([LogitechZ407InputSelect(coordinator)])


class LogitechZ407InputSelect(CoordinatorEntity[Z407Coordinator], SelectEntity):
    """Z407 input source select."""

    _attr_has_entity_name = True
    _attr_translation_key = "input_source"
    _attr_name = None
    _attr_options = [SOURCE_LABELS[source] for source in SOURCE_OPTIONS]

    def __init__(self, coordinator: Z407Coordinator) -> None:
        super().__init__(coordinator)
        self._client = coordinator.client
        self._attr_unique_id = f"{self._client.address}-input-source"
        self._current_option = None

    @property
    def device_info(self):
        return build_device_info(self._client.address)

    @property
    def available(self) -> bool:
        return self.coordinator.data.connected if self.coordinator.data else False

    @property
    def current_option(self):
        source = self.coordinator.data.input_source if self.coordinator.data else None
        if source is None:
            return self._current_option
        return SOURCE_LABELS.get(source, self._current_option)

    async def async_select_option(self, option: str) -> None:
        if not self.available:
            raise Z407ClientError(
                f"Cannot select input source: "
                f"Logitech Z407 ({self._client.address}) is not connected. "
                "Make sure the speaker is powered on and Bluetooth is available."
            )
        source = {
            SOURCE_LABELS[key]: key for key in SOURCE_OPTIONS
        }[option]
        try:
            await self._client.async_set_source(SOURCE_COMMANDS[source])
            self._current_option = option
            await self.coordinator.async_request_refresh()
        except Z407ClientError:
            raise
