"""Read-only operating and maintenance flags."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import EntityCategory

from .entity import VentsEntity

FLAGS = (
    ("boost_active", "coils", 3, None),
    ("fireplace_active", "coils", 4, None),
    ("heater_active", "discrete", 7, BinarySensorDeviceClass.RUNNING),
    ("heater_cooldown", "discrete", 9, BinarySensorDeviceClass.RUNNING),
    ("supply_filter_clogged", "discrete", 12, BinarySensorDeviceClass.PROBLEM),
    ("extract_filter_clogged", "discrete", 13, BinarySensorDeviceClass.PROBLEM),
    ("alarm", "alarm", 38, BinarySensorDeviceClass.PROBLEM),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(VentsBinarySensor(entry.runtime_data, *spec) for spec in FLAGS)


class VentsBinarySensor(VentsEntity, BinarySensorEntity):
    def __init__(self, coordinator, key, bank, address, device_class):
        super().__init__(coordinator, key)
        self.bank, self.address = bank, address
        self._attr_device_class = device_class
        if device_class == BinarySensorDeviceClass.PROBLEM:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self):
        if self.bank == "alarm":
            return self.data.inputs.get(38, 0) != 0 or bool(self.data.alarms)
        return getattr(self.data, self.bank).get(self.address)
