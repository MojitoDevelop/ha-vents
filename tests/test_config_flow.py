"""Check actual HA config/options flows, including endpoint duplicate checks."""

from unittest.mock import patch

from homeassistant import config_entries

from custom_components.vents_a21.const import DOMAIN
from custom_components.vents_a21.protocol import VentsClient


def quick_client(host, port, unit_id):
    return VentsClient(host, port, unit_id, timeout=0.2, connect_delay=0)


async def test_connection_flow_validates_identity_without_writes(hass, peer):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    with patch(
        "custom_components.vents_a21.config_flow.VentsClient", side_effect=quick_client
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "127.0.0.1", "port": peer.port, "unit_id": 1}
        )
    assert result["type"] == "create_entry"
    assert result["data"]["unit_id"] == 1
    assert peer.writes == []
    await hass.async_block_till_done()


async def test_wrong_identity_has_a_specific_error(hass, peer):
    peer.inputs[37] = 0
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    with patch(
        "custom_components.vents_a21.config_flow.VentsClient", side_effect=quick_client
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "127.0.0.1", "port": peer.port, "unit_id": 1}
        )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "unsupported_controller"}
    assert peer.writes == []


async def test_existing_endpoint_aborts_before_a_second_connection(
    hass, integration, peer
):
    count = len(peer.requests)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "127.0.0.1", "port": peer.port, "unit_id": 1}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert len(peer.requests) == count


async def test_invalid_hostname_stays_in_form(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "http://example.invalid", "port": 502, "unit_id": 1}
    )
    assert result["errors"] == {"host": "invalid_host"}


async def test_options_reload_exposes_selected_hardware(hass, integration):
    result = await hass.config_entries.options.async_init(integration.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "poll_interval": 15,
            "timeout": 5,
            "connect_delay": 0,
            "optional_sensors": ["co2"],
        },
    )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert integration.options["poll_interval"] == 15
    assert hass.states.get("sensor.vents_internal_co2").state == "800"
    assert integration.state == config_entries.ConfigEntryState.LOADED
