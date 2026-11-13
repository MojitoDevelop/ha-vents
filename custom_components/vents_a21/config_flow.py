"""Validate an A21 controller before adding it; never write during discovery."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONNECT_DELAY,
    CONF_OPTIONAL_SENSORS,
    CONF_POLL_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_CONNECT_DELAY,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    OPTIONAL_SENSORS,
)
from .protocol import UnsupportedController, VentsClient, VentsError

_LOGGER = logging.getLogger(__name__)


def connection_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(
                CONF_UNIT_ID, default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=16)),
        }
    )


async def validate_connection(data: dict) -> None:
    client = VentsClient(data[CONF_HOST], data[CONF_PORT], data[CONF_UNIT_ID])
    try:
        await client.async_validate()
    finally:
        await client.async_close()


class VentsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a local endpoint with a unit identity check."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VentsOptionsFlow()

    async def async_step_user(self, user_input=None):
        return await self._async_connection_step("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._async_connection_step("reconfigure", user_input)

    async def _async_connection_step(self, step, user_input):
        errors = {}
        entry = self._get_reconfigure_entry() if step == "reconfigure" else None
        defaults = dict(entry.data) if entry else {}
        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_HOST] = user_input[CONF_HOST].strip().lower()
            defaults.update(user_input)
            if (
                not user_input[CONF_HOST]
                or any(c.isspace() for c in user_input[CONF_HOST])
                or "://" in user_input[CONF_HOST]
            ):
                errors[CONF_HOST] = "invalid_host"
            else:
                endpoint = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_UNIT_ID]}"
                if any(
                    other.unique_id == endpoint
                    and (entry is None or other.entry_id != entry.entry_id)
                    for other in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                try:
                    if (
                        entry
                        and dict(entry.data) == user_input
                        and entry.state is config_entries.ConfigEntryState.LOADED
                    ):
                        await entry.runtime_data.client.async_validate()
                    else:
                        await validate_connection(user_input)
                except UnsupportedController:
                    errors["base"] = "unsupported_controller"
                except VentsError, OSError, ValueError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error validating a Vents controller")
                    errors["base"] = "unknown"
                else:
                    if entry:
                        self.hass.config_entries.async_update_entry(
                            entry, unique_id=endpoint
                        )
                        return self.async_update_reload_and_abort(
                            entry, data_updates=user_input
                        )
                    await self.async_set_unique_id(endpoint)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title="Vents", data=user_input)
        return self.async_show_form(
            step_id=step, data_schema=connection_schema(defaults), errors=errors
        )


class VentsOptionsFlow(config_entries.OptionsFlow):
    """Polling and optional hardware; defaults do not expose absent sensors."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=3, max=300)),
                    vol.Required(
                        CONF_TIMEOUT, default=options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                    vol.Required(
                        CONF_CONNECT_DELAY,
                        default=options.get(CONF_CONNECT_DELAY, DEFAULT_CONNECT_DELAY),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
                    vol.Required(
                        CONF_OPTIONAL_SENSORS,
                        default=options.get(CONF_OPTIONAL_SENSORS, []),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(OPTIONAL_SENSORS),
                            multiple=True,
                            translation_key="optional_sensors",
                        )
                    ),
                }
            ),
        )
