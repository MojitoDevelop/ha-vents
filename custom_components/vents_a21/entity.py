"""Shared entity identity and capability checks."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VentsCoordinator


class VentsEntity(CoordinatorEntity[VentsCoordinator]):
    """Use translated display names and stable English entity IDs."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: VentsCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Vents",
            model="A21 controller",
            name=entry.title,
            sw_version=self._firmware(),
        )

    def _firmware(self) -> str | None:
        raw = self.coordinator.data.inputs.get(34)
        return f"{raw & 255}.{raw >> 8}" if raw is not None else None

    @property
    def suggested_object_id(self) -> str:
        """Deliberately independent of the HA language and translated name."""
        return self._key

    @property
    def data(self):
        return self.coordinator.data
