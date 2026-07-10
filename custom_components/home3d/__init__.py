"""Integration bootstrap for Home3D."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .panel import async_setup_panel
from .views import async_setup_frontend_resources
from .websocket_api import async_setup_websocket_api

_LOGGER = logging.getLogger(__name__)
_SETUP_DONE_KEY = f"{__name__}.setup_done"


async def _async_initialize_once(hass: HomeAssistant) -> None:
    """Initialize HTTP resources and sidebar panel only once."""
    if hass.data.get(_SETUP_DONE_KEY):
        return

    _LOGGER.info("[Home3D] Registering HTTP resources")
    await async_setup_frontend_resources(hass)

    _LOGGER.info("[Home3D] Registering frontend")
    _LOGGER.info("[Home3D] Registering sidebar panel")
    await async_setup_panel(hass)
    _LOGGER.info("[Home3D] Sidebar panel registered")

    _LOGGER.info("[Home3D] Registering websocket API")
    await async_setup_websocket_api(hass)

    hass.data[_SETUP_DONE_KEY] = True


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Initialize Home3D integration and register resources and panel."""
    _ = config

    _LOGGER.info("[Home3D] async_setup()")
    await _async_initialize_once(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home3D from a config entry."""
    _ = entry
    _LOGGER.info("[Home3D] async_setup()")
    await _async_initialize_once(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Home3D config entry."""
    _ = hass
    _ = entry
    return True
