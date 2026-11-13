"""Correctly separate tenths-of-degrees measurements from integer setpoints."""

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import ServiceValidationError

from .entity import VentsEntity
from .protocol import Command

MODE_TO_REGISTER = {
    HVACMode.FAN_ONLY: 0,
    HVACMode.HEAT: 1,
    HVACMode.COOL: 2,
    HVACMode.AUTO: 3,
}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([VentsClimate(entry.runtime_data)])


class VentsClimate(VentsEntity, ClimateEntity):
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 15
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    _attr_precision = 0.1
    _attr_hvac_modes = [HVACMode.OFF, *MODE_TO_REGISTER]

    def __init__(self, coordinator):
        super().__init__(coordinator, "climate")

    @property
    def current_temperature(self):
        return self.data.temperature(0)

    @property
    def target_temperature(self):
        return self.data.holding.get(44)

    @property
    def hvac_mode(self):
        if not self.data.coils.get(0):
            return HVACMode.OFF
        return next(
            (
                mode
                for mode, value in MODE_TO_REGISTER.items()
                if value == self.data.holding.get(43)
            ),
            None,
        )

    async def async_set_temperature(self, **kwargs: Any):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if (
            temperature is None
            or not 15 <= temperature <= 30
            or int(temperature) != temperature
        ):
            raise ServiceValidationError(
                "Vents temperature must be a whole number from 15 to 30 °C"
            )
        await self.coordinator.async_command(Command("holding", 44, int(temperature)))

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode in MODE_TO_REGISTER:
            await self.coordinator.async_command(
                Command("holding", 43, MODE_TO_REGISTER[hvac_mode]),
                Command("coil", 0, True),
            )
        else:
            raise ServiceValidationError("Unsupported Vents HVAC mode")

    async def async_turn_on(self):
        await self.coordinator.async_command(Command("coil", 0, True))

    async def async_turn_off(self):
        await self.coordinator.async_command(Command("coil", 0, False))
