"""Config flow for Logitech Z407."""

from __future__ import annotations

import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN

BLE_MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class LogitechZ407ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Logitech Z407."""

    VERSION = 1
    discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        """Handle Bluetooth discovery."""

        address = discovery_info.address
        title = discovery_info.name or discovery_info.address
        self.discovered_devices[address] = title

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Show discovered devices or manual address entry."""
        errors = {}

        if self.discovered_devices:
            options = {
                address: title
                for address, title in sorted(self.discovered_devices.items())
            }
            schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(options)})
        else:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): str})

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        address = user_input[CONF_ADDRESS]

        if not self.discovered_devices:
            if not BLE_MAC_PATTERN.match(address):
                errors[CONF_ADDRESS] = "invalid_address"
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors=errors
                )
            address = address.upper()
            title = f"Logitech Z407 ({address})"
        else:
            title = options[address]

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data={CONF_ADDRESS: address})
