"""Panel registration module for Home3D."""

from __future__ import annotations

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import (
    PANEL_ICON,
    PANEL_MODULE_URL,
    PANEL_NAME,
    PANEL_TITLE,
    PANEL_WEB_COMPONENT_NAME,
)


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register the Home3D sidebar panel using official Home Assistant API."""
    if frontend.async_panel_exists(hass, PANEL_NAME):
        return

    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_NAME,
        webcomponent_name=PANEL_WEB_COMPONENT_NAME,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url=PANEL_MODULE_URL,
        embed_iframe=False,
        require_admin=False,
        config_panel_domain=None,
    )
