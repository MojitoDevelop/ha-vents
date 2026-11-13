"""Built-in schedule and timer activation."""

from typing import Any

from homeassistant.components.switch import SwitchEntity

from .entity import VentsEntity
from .protocol import Command


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            VentsSwitch(entry.runtime_data, "timer", 1),
            VentsSwitch(entry.runtime_data, "weekly_schedule", 2),
        ]
    )


class VentsSwitch(VentsEntity, SwitchEntity):
    def __init__(self, coordinator, key, address):
        super().__init__(coordinator, key)
        self.address = address

    @property
    def is_on(self):
        return self.data.coils.get(self.address)

    async def async_turn_on(self, **kwargs: Any):
        await self.coordinator.async_command(Command("coil", self.address, True))

    async def async_turn_off(self, **kwargs: Any):
        await self.coordinator.async_command(Command("coil", self.address, False))
