"""DataUpdateCoordinator for the Logitech Z407."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import Z407Client, Z407ClientError
from .const import DOMAIN, Z407State

_LOGGER = logging.getLogger(__name__)


class Z407Coordinator(DataUpdateCoordinator[Z407State]):
    """Periodic connection watchdog and state cache."""

    def __init__(self, hass: HomeAssistant, client: Z407Client) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.client = client

    async def _async_update_data(self) -> Z407State:
        try:
            return await self.client.async_refresh()
        except Z407ClientError as err:
            _LOGGER.warning("Z407 refresh failed: %s", err)
        except Exception as err:
            _LOGGER.warning("Unexpected error refreshing Z407: %s", err)
        return self.client.state
