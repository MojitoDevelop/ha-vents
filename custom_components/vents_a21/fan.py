"""Unit power, preset speeds, and balanced manual speed control."""

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.exceptions import ServiceValidationError

from .entity import VentsEntity
from .protocol import Command


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([VentsFan(entry.runtime_data)])


class VentsFan(VentsEntity, FanEntity):
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator):
        super().__init__(coordinator, "ventilation")

    @property
    def is_on(self):
        return self.data.coils.get(0)

    @property
    def preset_modes(self):
        maximum = min(5, max(3, self.data.holding[1]))
        return [f"speed_{n}" for n in range(1, maximum + 1)] + ["manual"]

    @property
    def preset_mode(self):
        value = self.data.holding.get(2)
        return (
            "manual"
            if value == 255
            else f"speed_{value}"
            if f"speed_{value}" in self.preset_modes
            else None
        )

    @property
    def percentage(self):
        if not self.is_on:
            return 0
        if self.data.holding.get(2) == 255:
            return self.data.holding.get(17)
        # A preset is a configured pair of airflows or fan outputs. Returning a
        # made-up percentage would confuse that preset with measured output.
        return None

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs: Any):
        if percentage is not None:
            await self.async_set_percentage(percentage)
        elif preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        else:
            await self.coordinator.async_command(Command("coil", 0, True))

    async def async_turn_off(self, **kwargs: Any):
        await self.coordinator.async_command(Command("coil", 0, False))

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
            return
        minimum, maximum = self.data.holding[3], self.data.holding[4]
        if not minimum <= percentage <= maximum:
            raise ServiceValidationError(
                f"Manual speed must be between {minimum} and {maximum}%"
            )
        await self.coordinator.async_command(
            Command("holding", 17, round(percentage)),
            Command("holding", 2, 255),
            Command("coil", 0, True),
        )

    async def async_set_preset_mode(self, preset_mode):
        if preset_mode not in self.preset_modes:
            raise ServiceValidationError("Unsupported Vents speed preset")
        value = (
            255 if preset_mode == "manual" else int(preset_mode.removeprefix("speed_"))
        )
        await self.coordinator.async_command(
            Command("holding", 2, value), Command("coil", 0, True)
        )
