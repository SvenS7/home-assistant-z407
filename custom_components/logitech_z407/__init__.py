"""Logitech Z407 integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import Z407Client, Z407ClientError
from .const import CONF_ADDRESS, DOMAIN
from .coordinator import Z407Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player", "select", "button"]

_RETRY_DELAYS = (1, 2, 4, 8)


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

    if not coordinator.data or not coordinator.data.connected:
        _LOGGER.debug("Z407 first refresh failed, retrying connection")
        for delay in _RETRY_DELAYS:
            await asyncio.sleep(delay)
            try:
                state = await client.async_refresh()
                if state.connected:
                    coordinator.data = state
                    _LOGGER.debug("Z407 connection succeeded on retry")
                    break
            except Z407ClientError:
                _LOGGER.debug(
                    "Z407 retry in %ss failed, %s retries left",
                    delay,
                    sum(1 for d in _RETRY_DELAYS if d > delay),
                )
        else:
            _LOGGER.warning(
                "Could not connect to Logitech Z407 (%s) after %d attempts. "
                "Make sure the speaker is powered on, in range, and not "
                "already connected to the physical remote.",
                address,
                len(_RETRY_DELAYS) + 1,
            )

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
