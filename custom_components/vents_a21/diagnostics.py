"""Download register diagnostics without disclosing the private endpoint."""


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "entry_id": entry.entry_id,
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "inputs": coordinator.data.inputs,
        "holding": coordinator.data.holding,
        "coils": coordinator.data.coils,
        "discrete": coordinator.data.discrete,
    }
