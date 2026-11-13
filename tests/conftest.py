"""Run the actual Home Assistant core against a local Modbus TCP peer."""

import asyncio

import pytest

from custom_components.vents_a21.const import DOMAIN

from .helpers import TestConfigEntry
from .server import ModbusPeer


@pytest.fixture
async def hass(tmp_path):
    from pathlib import Path

    from homeassistant import config_entries, loader
    from homeassistant.core import CoreState, HomeAssistant
    from homeassistant.helpers import (
        area_registry,
        category_registry,
        condition,
        device_registry,
        entity,
        entity_registry,
        floor_registry,
        frame,
        issue_registry,
        label_registry,
        translation,
        trigger,
    )
    from homeassistant.util.unit_system import METRIC_SYSTEM

    instance = HomeAssistant(str(tmp_path))
    instance.config.skip_pip = True
    instance.config.units = METRIC_SYSTEM
    instance.config_entries = config_entries.ConfigEntries(instance, {"test": {}})
    instance.config_entries._initialized.set()
    loader.async_setup(instance)
    import json

    component_path = Path(__file__).resolve().parents[1] / "custom_components/vents_a21"
    instance.data[loader.DATA_CUSTOM_COMPONENTS] = {
        DOMAIN: loader.Integration(
            instance,
            "custom_components.vents_a21",
            component_path,
            json.loads((component_path / "manifest.json").read_text()),
            top_level_files={path.name for path in component_path.iterdir()},
        )
    }
    entity.async_setup(instance)
    frame.async_setup(instance)
    translation.async_setup(instance)
    await condition.async_setup(instance)
    await trigger.async_setup(instance)
    device_registry.async_setup(instance)
    for registry in (
        area_registry,
        category_registry,
        device_registry,
        entity_registry,
        floor_registry,
        label_registry,
        issue_registry,
    ):
        await registry.async_load(instance, load_empty=True)
    instance.set_state(CoreState.running)
    try:
        yield instance
    finally:
        for entry in instance.config_entries.async_entries():
            if entry.state is config_entries.ConfigEntryState.LOADED:
                await asyncio.wait_for(
                    instance.config_entries.async_unload(entry.entry_id), 5
                )
        await asyncio.wait_for(instance.async_stop(force=True), 5)


@pytest.fixture
async def peer():
    server = await ModbusPeer().start()
    try:
        yield server
    finally:
        await server.close()


@pytest.fixture
async def integration(hass, peer):
    entry = TestConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1", "port": peer.port, "unit_id": 1},
        unique_id=f"127.0.0.1:{peer.port}:1",
        options={"connect_delay": 0},
    )
    entry.add_to_hass(hass)
    assert await asyncio.wait_for(hass.config_entries.async_setup(entry.entry_id), 10)
    await hass.async_block_till_done()
    return entry
