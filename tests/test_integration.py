"""Exercise services, entity state, lifecycle, and translations in real HA."""

import asyncio

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.vents_a21.const import DOMAIN

from .helpers import TestConfigEntry


async def service(hass, domain, name, entity_id, **data):
    await hass.services.async_call(
        domain, name, {"entity_id": entity_id, **data}, blocking=True
    )
    await hass.async_block_till_done()


async def test_default_measurements_and_no_boot_writes(hass, integration, peer):
    assert hass.states.get("sensor.vents_outdoor_air_temperature").state == "-4.5"
    assert hass.states.get("sensor.vents_supply_air_temperature").state == "20.5"
    assert hass.states.get("sensor.vents_temperature_setpoint").state == "23"
    assert hass.states.get("sensor.vents_supply_fan_output").state == "45"
    assert hass.states.get("sensor.vents_internal_co2") is None
    assert peer.writes == []
    climate = hass.states.get("climate.vents_climate")
    assert climate.attributes["temperature"] == 23
    assert climate.attributes["current_temperature"] == 21.5
    assert climate.attributes["min_temp"] == 15
    assert climate.attributes["max_temp"] == 30
    assert climate.state == "auto"


async def test_temperature_writes_whole_degrees(hass, integration, peer):
    await service(
        hass, "climate", "set_temperature", "climate.vents_climate", temperature=24
    )
    assert peer.writes == [(6, 44, 24)]
    assert hass.states.get("climate.vents_climate").attributes["temperature"] == 24
    assert hass.states.get("number.vents_target_temperature").state == "24"
    assert hass.states.get("sensor.vents_temperature_setpoint").state == "24"


async def test_hvac_and_power_use_distinct_register_and_coil(hass, integration, peer):
    await service(
        hass, "climate", "set_hvac_mode", "climate.vents_climate", hvac_mode="heat"
    )
    assert peer.writes == [(6, 43, 1), (5, 0, 0xFF00)]
    await service(hass, "fan", "turn_off", "fan.vents_ventilation")
    assert peer.writes[-1] == (5, 0, 0)
    assert hass.states.get("climate.vents_climate").state == "off"


async def test_manual_speed_order_and_preset(hass, integration, peer):
    await service(hass, "fan", "set_percentage", "fan.vents_ventilation", percentage=65)
    assert peer.writes == [(6, 17, 65), (6, 2, 255), (5, 0, 0xFF00)]
    assert hass.states.get("fan.vents_ventilation").attributes["percentage"] == 65
    await service(
        hass, "fan", "set_preset_mode", "fan.vents_ventilation", preset_mode="speed_3"
    )
    assert peer.writes[-2:] == [(6, 2, 3), (5, 0, 0xFF00)]
    assert (
        hass.states.get("fan.vents_ventilation").attributes["preset_mode"] == "speed_3"
    )


async def test_analog_bypass_manual_setpoint_and_mode(hass, integration, peer):
    await service(
        hass, "number", "set_value", "number.vents_bypass_position_setpoint", value=35
    )
    await service(
        hass, "select", "select_option", "select.vents_bypass_mode", option="manual"
    )
    assert peer.writes == [(6, 75, 35), (6, 74, 1)]
    # Commanded opening and reported opening are intentionally separate.
    assert hass.states.get("sensor.vents_bypass_position").state == "25"
    assert hass.states.get("sensor.vents_bypass_setpoint").state == "35"


async def test_discrete_bypass_does_not_expose_an_analog_control(
    hass, integration, peer
):
    peer.holding[57] = 1
    await integration.runtime_data.async_refresh()
    assert (
        hass.states.get("number.vents_bypass_position_setpoint").state == "unavailable"
    )
    assert hass.states.get("select.vents_bypass_mode").attributes["options"] == [
        "closed",
        "open",
        "auto",
    ]
    await service(
        hass, "select", "select_option", "select.vents_bypass_mode", option="open"
    )
    assert peer.writes == [(6, 74, 1)]


async def test_native_timer_and_schedule(hass, integration, peer):
    await service(hass, "number", "set_value", "number.vents_timer_duration", value=90)
    assert peer.writes == [(6, 51, 0x1E01)]
    assert hass.states.get("number.vents_timer_duration").state == "90"
    await service(
        hass, "select", "select_option", "select.vents_timer_speed", option="speed_3"
    )
    await service(hass, "switch", "turn_on", "switch.vents_timer")
    await service(hass, "switch", "turn_on", "switch.vents_weekly_schedule")
    assert peer.writes[-3:] == [(6, 49, 3), (5, 1, 0xFF00), (5, 2, 0xFF00)]


@pytest.mark.parametrize(
    "entity,value",
    [
        ("target_temperature", 23.5),
        ("timer_temperature", 10),
        ("filter_timer_period", 30),
        ("manual_speed", 10),
    ],
)
async def test_reject_invalid_setpoints_without_writing(
    hass, integration, peer, entity, value
):
    with pytest.raises(HomeAssistantError):
        await service(
            hass, "number", "set_value", f"number.vents_{entity}", value=value
        )
    assert peer.writes == []


async def test_sensor_faults_and_alarm_details(hass, integration, peer):
    peer.inputs[2] = 0x8000
    peer.inputs[38] = 2
    peer.discrete[19 + 40] = True
    await integration.runtime_data.async_refresh()
    assert hass.states.get("sensor.vents_supply_air_temperature").state == "unavailable"
    assert hass.states.get("binary_sensor.vents_alarm").state == "on"
    state = hass.states.get("sensor.vents_alarm_status")
    assert state.state == "warning"
    assert state.attributes["active_codes"] == [40]
    assert "filter" in state.attributes["descriptions"][0].lower()
    await service(hass, "button", "press", "button.vents_reset_alarms")
    assert peer.writes == [(5, 18, 0xFF00)]
    assert hass.states.get("binary_sensor.vents_alarm").state == "off"


async def test_missing_connection_and_recovery(hass, integration, peer):
    peer.fail_reads = True
    await integration.runtime_data.async_refresh()
    assert hass.states.get("fan.vents_ventilation").state == "unavailable"
    assert (
        hass.states.get("sensor.vents_outdoor_air_temperature").state == "unavailable"
    )
    peer.fail_reads = False
    await integration.runtime_data.async_refresh()
    assert hass.states.get("sensor.vents_outdoor_air_temperature").state == "-4.5"
    assert peer.writes == []


async def test_failed_write_marks_state_unavailable(hass, integration, peer):
    peer.reject_write = True
    with pytest.raises(HomeAssistantError):
        await service(
            hass, "climate", "set_temperature", "climate.vents_climate", temperature=24
        )
    assert hass.states.get("climate.vents_climate").state == "unavailable"
    assert len([r for r in peer.requests if r[0] == 6]) == 1


@pytest.mark.parametrize(
    "language,expected",
    [("en", "Outdoor air temperature"), ("pl", "Temperatura czerpni")],
)
async def test_display_translation_keeps_english_entity_ids(
    hass, peer, language, expected
):
    hass.config.language = language
    entry = TestConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1", "port": peer.port, "unit_id": 1},
        options={"connect_delay": 0},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.vents_outdoor_air_temperature")
    assert state is not None
    assert expected in state.name
    registry = er.async_get(hass)
    assert (
        registry.async_get("sensor.vents_outdoor_air_temperature").original_name
        == expected
    )
    assert peer.writes == []


async def test_optional_hardware_is_explicit_and_missing_sensors_are_unavailable(
    hass, peer
):
    entry = TestConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1", "port": peer.port, "unit_id": 1},
        options={"connect_delay": 0, "optional_sensors": ["co2", "airflow"]},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.vents_internal_co2").state == "800"
    assert hass.states.get("sensor.vents_external_co2").state == "unavailable"
    assert hass.states.get("sensor.vents_supply_airflow").state == "180"
    await service(hass, "number", "set_value", "number.vents_co2_setpoint", value=1000)
    assert peer.writes == [(6, 46, 1000)]


async def test_unload_closes_the_only_connection(hass, integration, peer):
    assert len(peer.writers) == 1
    assert await hass.config_entries.async_unload(integration.entry_id)
    await hass.async_block_till_done()
    await asyncio.wait_for(peer.disconnected.wait(), 1)
    assert not peer.writers
