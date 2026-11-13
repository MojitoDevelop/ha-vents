"""Local Home Assistant integration for Vents A21 ventilation units."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TIMEOUT
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CONNECT_DELAY,
    CONF_UNIT_ID,
    DEFAULT_CONNECT_DELAY,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    PLATFORMS,
)
from .coordinator import VentsCoordinator
from .protocol import VentsClient

type VentsConfigEntry = ConfigEntry[VentsCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: VentsConfigEntry) -> bool:
    """Open one connection, read first, then create entities."""
    client = VentsClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
        entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
        entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        entry.options.get(CONF_CONNECT_DELAY, DEFAULT_CONNECT_DELAY),
    )
    entry.async_on_unload(client.async_close)
    coordinator = entry.runtime_data = VentsCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: VentsConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: VentsConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
