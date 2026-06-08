"""Number platform for Logitech Z407 bass level control."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Z407ClientError
from .const import BASS_STEPS, BUTTON_COMMANDS, DOMAIN, build_device_info
from .coordinator import Z407Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities."""

    coordinator: Z407Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([LogitechZ407BassLevel(coordinator)])


class LogitechZ407BassLevel(CoordinatorEntity[Z407Coordinator], NumberEntity):
    """Bass level slider mapped to 0-100% (0-15 steps on the speaker)."""

    _attr_has_entity_name = True
    _attr_translation_key = "bass_level"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: Z407Coordinator) -> None:
        super().__init__(coordinator)
        self._client = coordinator.client
        self._attr_unique_id = f"{self._client.address}-bass-level"

    @property
    def device_info(self):
        return build_device_info(self._client.address)

    @property
    def available(self) -> bool:
        return self.coordinator.data.connected if self.coordinator.data else False

    @property
    def native_value(self) -> float | None:
        if self._client.state.bass_level is not None:
            return round(self._client.state.bass_level / BASS_STEPS * 100)
        return None

    async def async_set_native_value(self, value: float) -> None:
        target_pct = max(0, min(100, int(value)))
        target_level = round(target_pct / 100 * BASS_STEPS)
        current_level = self._client.state.bass_level

        if current_level is None:
            raise Z407ClientError(
                "Bass level is unknown. Press the calibrate button first."
            )

        delta = target_level - current_level
        if delta == 0:
            return

        command = BUTTON_COMMANDS["bass_up" if delta > 0 else "bass_down"]
        for _ in range(abs(delta)):
            await self._client.async_send_command(command)

        self._client.state.bass_level = target_level
        self.async_write_ha_state()
