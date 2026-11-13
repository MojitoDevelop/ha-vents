"""Coordinate one complete scan and read back every command."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN
from .protocol import Command, Snapshot, VentsClient, VentsError

_LOGGER = logging.getLogger(__name__)


class VentsCoordinator(DataUpdateCoordinator[Snapshot]):
    """Keep all platforms in agreement after a write or refresh."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: VentsClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            ),
        )
        self.client = client
        self._transaction = asyncio.Lock()

    async def _async_update_data(self) -> Snapshot:
        async with self._transaction:
            try:
                return await self.client.async_read()
            except VentsError as err:
                raise UpdateFailed(str(err)) from err

    async def async_command(self, *commands: Command) -> None:
        async with self._transaction:
            try:
                snapshot = await self.client.async_execute(list(commands))
            except VentsError as err:
                self.async_set_update_error(UpdateFailed(str(err)))
                raise HomeAssistantError(f"Vents command failed: {err}") from err
            self.async_set_updated_data(snapshot)
