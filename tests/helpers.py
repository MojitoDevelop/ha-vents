"""Real config entries with explicit defaults for supported HA versions."""

from types import MappingProxyType

from homeassistant import config_entries


class TestConfigEntry(config_entries.ConfigEntry):
    __test__ = False

    def __init__(self, *, domain, data, title="Vents", unique_id=None, options=None):
        super().__init__(
            version=1,
            minor_version=1,
            domain=domain,
            data=data,
            title=title,
            unique_id=unique_id,
            options=options or {},
            source="user",
            discovery_keys=MappingProxyType({}),
            subentries_data=(),
        )

    def add_to_hass(self, hass):
        hass.config_entries._entries[self.entry_id] = self
