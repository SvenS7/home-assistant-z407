"""Logitech Z407 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import Z407Client
from .const import CONF_ADDRESS, DOMAIN
from .coordinator import Z407Coordinator

PLATFORMS = ["media_player", "select", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Logitech Z407 from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    address = entry.data[CONF_ADDRESS]
    client = Z407Client(hass, address, entry.title)
    coordinator = Z407Coordinator(hass, client)
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        client: Z407Client = entry_data["client"]
        await client.async_disconnect()
    return unload_ok
