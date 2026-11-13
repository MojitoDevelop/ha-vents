"""Writable setpoints, including a correctly packed native timer duration."""

import math
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_OPTIONAL_SENSORS
from .entity import VentsEntity
from .protocol import Command


@dataclass(frozen=True)
class NumberSpec:
    key: str
    address: int
    minimum: int
    maximum: int
    unit: str | None = None
    feature: str | None = None
    preset: int | None = None
    ventilation_mode: int | None = None


NUMBERS = (
    NumberSpec("manual_speed", 17, 0, 100, PERCENTAGE),
    NumberSpec("bypass_position_setpoint", 75, 0, 100, PERCENTAGE),
    NumberSpec("target_temperature", 44, 15, 30, UnitOfTemperature.CELSIUS),
    NumberSpec("timer_duration", 51, 1, 1439, UnitOfTime.MINUTES),
    NumberSpec("timer_temperature", 50, 0, 30, UnitOfTemperature.CELSIUS),
    NumberSpec("filter_timer_period", 58, 0, 365, UnitOfTime.DAYS),
    NumberSpec("humidity_setpoint", 45, 40, 80, PERCENTAGE, "humidity"),
    NumberSpec("co2_setpoint", 46, 400, 2000, "ppm", "co2"),
    NumberSpec("pm25_setpoint", 47, 100, 1000, "µg/m³", "pm25"),
    NumberSpec("voc_setpoint", 48, 20, 100, PERCENTAGE, "voc"),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    features = entry.options.get(CONF_OPTIONAL_SENSORS, [])
    specs = [
        spec for spec in NUMBERS if spec.feature is None or spec.feature in features
    ]
    maximum = min(5, max(3, coordinator.data.holding[1]))
    for speed in range(1, maximum + 1):
        for offset, direction in enumerate(("supply", "extract")):
            specs.append(
                NumberSpec(
                    f"speed_{speed}_{direction}_output",
                    7 + (speed - 1) * 2 + offset,
                    0,
                    100,
                    PERCENTAGE,
                    preset=speed,
                    ventilation_mode=0,
                )
            )
            specs.append(
                NumberSpec(
                    f"speed_{speed}_{direction}_airflow",
                    27 + (speed - 1) * 2 + offset,
                    0,
                    10000,
                    UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                    preset=speed,
                    ventilation_mode=1,
                )
            )
    async_add_entities(VentsNumber(coordinator, spec) for spec in specs)


class VentsNumber(VentsEntity, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    def __init__(self, coordinator, spec):
        super().__init__(coordinator, spec.key)
        self.spec = spec
        self._attr_native_unit_of_measurement = spec.unit
        if spec.key not in (
            "manual_speed",
            "target_temperature",
            "bypass_position_setpoint",
        ):
            self._attr_entity_category = EntityCategory.CONFIG
        if spec.preset:
            self._attr_entity_registry_enabled_default = False

    @property
    def native_min_value(self):
        if self.spec.key == "manual_speed":
            return self.data.holding[3]
        if self.spec.ventilation_mode == 1:
            return self.data.holding[23]
        return self.spec.minimum

    @property
    def native_max_value(self):
        if self.spec.key == "manual_speed":
            return self.data.holding[4]
        if self.spec.ventilation_mode == 1:
            return self.data.holding[24]
        return self.spec.maximum

    @property
    def native_value(self):
        value = self.data.holding.get(self.spec.address)
        if value is None:
            return None
        if self.spec.key == "timer_duration":
            hours, minutes = value & 255, value >> 8
            return hours * 60 + minutes if hours <= 23 and minutes <= 59 else None
        return value

    @property
    def available(self):
        if not super().available:
            return False
        if (
            self.spec.key == "bypass_position_setpoint"
            and self.data.holding.get(57) != 2
        ):
            return False
        if self.spec.ventilation_mode is not None:
            return self.data.holding.get(0) == self.spec.ventilation_mode
        return True

    async def async_set_native_value(self, value):
        if (
            not math.isfinite(value)
            or int(value) != value
            or not self.native_min_value <= value <= self.native_max_value
        ):
            raise ServiceValidationError(
                "Value outside the controller's supported range"
            )
        value = int(value)
        if self.spec.key == "filter_timer_period" and 0 < value < 70:
            raise ServiceValidationError(
                "The filter timer accepts 0 (disabled) or 70–365 days"
            )
        if self.spec.key == "timer_temperature" and 0 < value < 15:
            raise ServiceValidationError(
                "Timer temperature accepts 0 (ventilation only) or 15–30 °C"
            )
        if not self.available:
            raise ServiceValidationError(
                "This setpoint is not supported by the current hardware/mode"
            )
        if self.spec.key == "timer_duration":
            hours, minutes = divmod(value, 60)
            value = hours | (minutes << 8)
        await self.coordinator.async_command(
            Command("holding", self.spec.address, value)
        )
