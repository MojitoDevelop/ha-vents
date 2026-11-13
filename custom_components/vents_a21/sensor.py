"""Measurements, setpoint mirrors, filter timers, and alarm diagnostics."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.helpers.entity import EntityCategory

from .alarms import alarm_description
from .const import CONF_OPTIONAL_SENSORS
from .entity import VentsEntity


@dataclass(frozen=True)
class SensorSpec:
    key: str
    address: int = 0
    kind: str = "input"
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    feature: str | None = None
    diagnostic: bool = False


SENSORS = (
    *(
        SensorSpec(
            key,
            address,
            "temperature",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
        )
        for key, address in (
            ("control_temperature", 0),
            ("outdoor_air_temperature", 1),
            ("supply_air_temperature", 2),
            ("extract_air_temperature", 3),
            ("exhaust_air_temperature", 4),
        )
    ),
    SensorSpec("manual_speed_setpoint", 17, "holding", PERCENTAGE),
    SensorSpec(
        "temperature_setpoint",
        44,
        "holding",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
    ),
    SensorSpec("bypass_setpoint", 75, "holding", PERCENTAGE),
    SensorSpec("speed_mode", 2, "holding", diagnostic=True),
    SensorSpec("bypass_mode_raw", 74, "holding", diagnostic=True),
    SensorSpec("bypass_position", 51, unit=PERCENTAGE),
    SensorSpec("supply_fan_output", 52, unit=PERCENTAGE),
    SensorSpec("extract_fan_output", 53, unit=PERCENTAGE),
    SensorSpec("heater_control_signal", 44, unit=PERCENTAGE, diagnostic=True),
    SensorSpec("filter_status", 31, "filter", diagnostic=True),
    SensorSpec(
        "filter_time_remaining",
        27,
        "duration",
        UnitOfTime.HOURS,
        SensorDeviceClass.DURATION,
        diagnostic=True,
    ),
    SensorSpec(
        "operating_time",
        29,
        "duration",
        UnitOfTime.HOURS,
        SensorDeviceClass.DURATION,
        diagnostic=True,
    ),
    SensorSpec(
        "timer_time_remaining",
        25,
        "timer",
        UnitOfTime.SECONDS,
        SensorDeviceClass.DURATION,
    ),
    SensorSpec("alarm_status", 38, "alarm", diagnostic=True),
    SensorSpec("active_alarm", 38, "active_alarm", diagnostic=True),
    SensorSpec(
        "internal_humidity",
        10,
        "optional",
        PERCENTAGE,
        SensorDeviceClass.HUMIDITY,
        "humidity",
    ),
    SensorSpec(
        "external_humidity",
        11,
        "optional",
        PERCENTAGE,
        SensorDeviceClass.HUMIDITY,
        "humidity",
    ),
    SensorSpec("internal_co2", 12, "optional", "ppm", SensorDeviceClass.CO2, "co2"),
    SensorSpec("external_co2", 13, "optional", "ppm", SensorDeviceClass.CO2, "co2"),
    SensorSpec(
        "internal_pm25", 14, "optional", "µg/m³", SensorDeviceClass.PM25, "pm25"
    ),
    SensorSpec(
        "external_pm25", 15, "optional", "µg/m³", SensorDeviceClass.PM25, "pm25"
    ),
    SensorSpec("internal_voc", 16, "optional", PERCENTAGE, feature="voc"),
    SensorSpec("external_voc", 17, "optional", PERCENTAGE, feature="voc"),
    SensorSpec(
        "supply_airflow",
        19,
        unit=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        feature="airflow",
    ),
    SensorSpec(
        "extract_airflow",
        20,
        unit=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        feature="airflow",
    ),
    SensorSpec(
        "supply_pressure",
        21,
        unit=UnitOfPressure.PA,
        device_class=SensorDeviceClass.PRESSURE,
        feature="pressure",
    ),
    SensorSpec(
        "extract_pressure",
        22,
        unit=UnitOfPressure.PA,
        device_class=SensorDeviceClass.PRESSURE,
        feature="pressure",
    ),
    SensorSpec("supply_fan_speed", 23, unit="rpm", feature="rpm"),
    SensorSpec("extract_fan_speed", 24, unit="rpm", feature="rpm"),
    *(
        SensorSpec(
            key,
            address,
            "temperature",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            "extra_temperature",
        )
        for key, address in (
            ("external_temperature", 5),
            ("after_preheater_temperature", 6),
            ("before_reheater_temperature", 7),
        )
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    features = entry.options.get(CONF_OPTIONAL_SENSORS, [])
    async_add_entities(
        VentsSensor(entry.runtime_data, spec)
        for spec in SENSORS
        if spec.feature is None or spec.feature in features
    )


class VentsSensor(VentsEntity, SensorEntity):
    def __init__(self, coordinator, spec):
        super().__init__(coordinator, spec.key)
        self.spec = spec
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_device_class = spec.device_class
        if spec.unit:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if spec.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if spec.kind in ("filter", "alarm"):
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = (
                ["clean", "supply", "extract", "both_or_timer"]
                if spec.kind == "filter"
                else ["none", "alarm", "warning"]
            )
        if spec.kind == "active_alarm":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["none", *[f"code_{n}" for n in range(53)]]

    @property
    def native_value(self):
        kind, address = self.spec.kind, self.spec.address
        if kind == "temperature":
            return self.data.temperature(address)
        if kind == "holding":
            return self.data.holding.get(address)
        if kind == "duration":
            return self.data.duration_hours(address)
        if kind == "timer":
            return self.data.timer_remaining
        if kind == "active_alarm":
            return f"code_{self.data.alarms[0]}" if self.data.alarms else "none"
        value = self.data.inputs.get(address)
        if kind == "optional":
            return (
                value if value else None
            )  # A21 explicitly uses zero for a missing air-quality sensor.
        if kind in ("filter", "alarm"):
            return (
                self._attr_options[value]
                if value is not None and 0 <= value < len(self._attr_options)
                else None
            )
        if address in (51, 52, 53) and (value is None or not 0 <= value <= 100):
            return None
        return value

    @property
    def available(self):
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self):
        if self.spec.kind in ("alarm", "active_alarm"):
            return {
                "active_codes": self.data.alarms,
                "discrete_input_addresses": [code + 19 for code in self.data.alarms],
                "descriptions": [
                    alarm_description(code, self.hass.config.language)
                    for code in self.data.alarms
                ],
            }
        if self.spec.key == "heater_control_signal":
            return {"fan_assistance_active": self.data.inputs.get(44, 0) > 100}
        return None
