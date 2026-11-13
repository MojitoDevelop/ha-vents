"""Read/write modes, with bypass capability checked against HR57."""

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityCategory

from .entity import VentsEntity
from .protocol import Command


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            VentsSelect(entry.runtime_data, "bypass_mode", 74),
            VentsSelect(entry.runtime_data, "timer_speed", 49),
        ]
    )


class VentsSelect(VentsEntity, SelectEntity):
    def __init__(self, coordinator, key, address):
        super().__init__(coordinator, key)
        self.address = address
        if key == "timer_speed":
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def _mapping(self):
        if self.address == 74:
            return {
                "closed": 0,
                "manual" if self.data.holding.get(57) == 2 else "open": 1,
                "auto": 2,
            }
        return {
            "standby": 0,
            **{
                f"speed_{n}": n
                for n in range(1, min(5, max(3, self.data.holding[1])) + 1)
            },
        }

    @property
    def options(self):
        return list(self._mapping)

    @property
    def current_option(self):
        return next(
            (
                key
                for key, value in self._mapping.items()
                if value == self.data.holding.get(self.address)
            ),
            None,
        )

    @property
    def available(self):
        return super().available and (
            self.address != 74 or self.data.holding.get(57) in (1, 2, 5)
        )

    async def async_select_option(self, option):
        if option not in self._mapping:
            raise ServiceValidationError("Unsupported Vents option")
        await self.coordinator.async_command(
            Command("holding", self.address, self._mapping[option])
        )
