"""Media player platform for Logitech Z407."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Z407ClientError
from .const import DOMAIN, MEDIA_COMMANDS, MEDIA_FEATURES, build_device_info
from .coordinator import Z407Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player entity."""

    coordinator: Z407Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([LogitechZ407MediaPlayer(coordinator)])


class LogitechZ407MediaPlayer(CoordinatorEntity[Z407Coordinator], MediaPlayerEntity):
    """Z407 media player entity."""

    _attr_has_entity_name = True
    _attr_translation_key = "speaker"
    _attr_name = None
    _attr_supported_features = MEDIA_FEATURES

    def __init__(self, coordinator: Z407Coordinator) -> None:
        super().__init__(coordinator)
        self._client = coordinator.client
        self._attr_unique_id = f"{self._client.address}-media-player"

    @property
    def device_info(self):
        return build_device_info(self._client.address)

    @property
    def available(self) -> bool:
        return self.coordinator.data.connected if self.coordinator.data else False

    @property
    def state(self) -> str | None:
        if self.coordinator.data and self.coordinator.data.connected:
            return MediaPlayerState.IDLE
        return None

    async def async_media_play(self) -> None:
        await self._async_send("media_play_pause")

    async def async_media_pause(self) -> None:
        await self._async_send("media_play_pause")

    async def async_media_play_pause(self) -> None:
        await self._async_send("media_play_pause")

    async def async_media_next_track(self) -> None:
        await self._async_send("media_next_track")

    async def async_media_previous_track(self) -> None:
        await self._async_send("media_previous_track")

    async def async_volume_up(self) -> None:
        await self._async_send("volume_up")

    async def async_volume_down(self) -> None:
        await self._async_send("volume_down")

    async def _async_send(self, action: str) -> None:
        if not self.available:
            raise Z407ClientError(
                f"Cannot {action.replace('_', ' ')}: "
                f"Logitech Z407 ({self._client.address}) is not connected. "
                "Make sure the speaker is powered on and Bluetooth is available."
            )
        try:
            await self._client.async_send_command(MEDIA_COMMANDS[action])
            await self.coordinator.async_request_refresh()
        except Z407ClientError:
            raise
