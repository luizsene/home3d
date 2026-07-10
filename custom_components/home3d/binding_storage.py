"""Persistent storage for Home3D model/entity bindings."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import BINDING_CONFIG_VERSION, BINDING_STORAGE_KEY, BINDING_STORAGE_VERSION


class BindingEntry(TypedDict, total=False):
    """Binding entry for model object."""

    entity_id: str
    entities: list[str]
    display_name: str
    metadata: dict[str, Any]


class BindingConfig(TypedDict):
    """Binding configuration persisted in Home Assistant storage."""

    version: int
    bindings: dict[str, BindingEntry]


class MultiModelBindingConfig(TypedDict):
    """Binding configuration persisted per model file."""

    version: int
    model_bindings: dict[str, BindingConfig]


DEFAULT_BINDING_CONFIG: BindingConfig = {
    "version": BINDING_CONFIG_VERSION,
    "bindings": {},
}

DEFAULT_MULTI_MODEL_BINDING_CONFIG: MultiModelBindingConfig = {
    "version": 2,
    "model_bindings": {},
}

DEFAULT_MODEL_FILE = "casa_demo.glb"


class Home3DBindingStorage:
    """Wrap Home Assistant Store for Home3D binding configuration."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass,
            BINDING_STORAGE_VERSION,
            BINDING_STORAGE_KEY,
        )

    def _normalize_single(self, payload: dict[str, Any] | None) -> BindingConfig:
        if not isinstance(payload, dict):
            return deepcopy(DEFAULT_BINDING_CONFIG)

        version = payload.get("version")
        bindings = payload.get("bindings")
        if not isinstance(version, int) or not isinstance(bindings, dict):
            return deepcopy(DEFAULT_BINDING_CONFIG)

        normalized: BindingConfig = {
            "version": BINDING_CONFIG_VERSION,
            "bindings": {},
        }

        for object_id, raw_entry in bindings.items():
            if not isinstance(object_id, str) or not isinstance(raw_entry, dict):
                continue

            entry: BindingEntry = {
                "metadata": {},
            }

            entity_id = raw_entry.get("entity_id")
            if isinstance(entity_id, str) and entity_id:
                entry["entity_id"] = entity_id

            entities = raw_entry.get("entities")
            if isinstance(entities, list):
                valid_entities = [item for item in entities if isinstance(item, str) and item]
                if valid_entities:
                    entry["entities"] = valid_entities

            display_name = raw_entry.get("display_name")
            if isinstance(display_name, str) and display_name:
                entry["display_name"] = display_name

            metadata = raw_entry.get("metadata")
            if isinstance(metadata, dict):
                entry["metadata"] = metadata

            if "entity_id" in entry or "entities" in entry:
                normalized["bindings"][object_id] = entry

        return normalized

    def _normalize_multi(self, payload: dict[str, Any] | None) -> MultiModelBindingConfig:
        if not isinstance(payload, dict):
            return deepcopy(DEFAULT_MULTI_MODEL_BINDING_CONFIG)

        model_bindings = payload.get("model_bindings")
        if isinstance(model_bindings, dict):
            normalized: MultiModelBindingConfig = {
                "version": 2,
                "model_bindings": {},
            }

            for model_file, raw_config in model_bindings.items():
                if not isinstance(model_file, str):
                    continue

                normalized["model_bindings"][model_file] = self._normalize_single(raw_config)

            return normalized

        legacy_single = self._normalize_single(payload)
        if legacy_single["bindings"]:
            return {
                "version": 2,
                "model_bindings": {
                    DEFAULT_MODEL_FILE: legacy_single,
                },
            }

        return deepcopy(DEFAULT_MULTI_MODEL_BINDING_CONFIG)

    async def async_load(self) -> MultiModelBindingConfig:
        """Load multi-model binding config from storage and normalize payload."""
        stored = await self._store.async_load()
        return self._normalize_multi(stored)

    async def async_load_for_model(self, model_file: str) -> BindingConfig:
        """Load one model binding document."""
        multi = await self.async_load()
        return deepcopy(multi["model_bindings"].get(model_file, DEFAULT_BINDING_CONFIG))

    async def async_save(self, config: dict[str, Any]) -> None:
        """Persist binding config payload, accepting legacy and multi-model schema."""
        normalized = self._normalize_multi(config)
        await self._store.async_save(normalized)

    async def async_save_for_model(self, model_file: str, config: BindingConfig) -> None:
        """Persist one model binding document into multi-model storage."""
        multi = await self.async_load()
        multi["model_bindings"][model_file] = self._normalize_single(config)
        await self._store.async_save(multi)
