"""Service registration placeholders for Home3D."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant


@dataclass(frozen=True, slots=True)
class Home3DServiceDefinition:
    """Describes a future Home3D service contract."""

    service_name: str
    description: str


PLACEHOLDER_SERVICES: tuple[Home3DServiceDefinition, ...] = (
    Home3DServiceDefinition(
        service_name="reserved",
        description="No services are implemented in this stage.",
    ),
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Reserve service setup hook without registering any services."""
    _ = hass


async def async_unload_services(hass: HomeAssistant) -> None:
    """Reserve service unload hook without unregistering services."""
    _ = hass
