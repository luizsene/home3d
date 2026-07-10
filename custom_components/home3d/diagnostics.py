"""Diagnostics placeholders for Home3D."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return a static diagnostics payload placeholder."""
    _ = hass
    _ = entry
    return {"status": "not_implemented"}
