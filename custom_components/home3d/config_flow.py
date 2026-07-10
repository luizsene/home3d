"""Config flow scaffold for Home3D."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import CONF_ADMIN_PASSWORD, DOMAIN


class Home3DConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Home3D config flow lifecycle."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "Home3DOptionsFlow":
        """Return the options flow handler."""
        return Home3DOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Create a single Home3D config entry for panel registration."""
        _ = user_input

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="Home3D", data={})


class Home3DOptionsFlow(config_entries.OptionsFlow):
    """Handle Home3D integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage Home3D options."""
        if user_input is not None:
            password = str(user_input.get(CONF_ADMIN_PASSWORD, "")).strip()
            return self.async_create_entry(
                title="",
                data={CONF_ADMIN_PASSWORD: password},
            )

        current_password = str(self._config_entry.options.get(CONF_ADMIN_PASSWORD, ""))
        schema = vol.Schema(
            {
                vol.Required(CONF_ADMIN_PASSWORD, default=current_password): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
