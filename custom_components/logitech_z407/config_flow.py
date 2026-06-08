"""Config flow for Logitech Z407."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN


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
        return self.async_create_entry(
            title=title,
            data={CONF_ADDRESS: address},
        )

    async def async_step_user(self, user_input=None):
        """Show discovered devices for manual setup."""

        if not self.discovered_devices:
            return self.async_abort(reason="no_devices_found")

        options = {
            address: title for address, title in sorted(self.discovered_devices.items())
        }
        schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(options)})

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        address = user_input[CONF_ADDRESS]
        title = options[address]
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data={CONF_ADDRESS: address})
