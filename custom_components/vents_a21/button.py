"""Explicit maintenance commands. No factory-reset button is exposed."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import VentsEntity
from .protocol import Command


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            VentsButton(entry.runtime_data, "reset_filter_timer", 17),
            VentsButton(entry.runtime_data, "reset_alarms", 18),
        ]
    )


class VentsButton(VentsEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, key, address):
        super().__init__(coordinator, key)
        self.address = address

    async def async_press(self):
        await self.coordinator.async_command(Command("coil", self.address, True))
