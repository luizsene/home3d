"""HTTP resource registration for Home3D frontend assets."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.core import HomeAssistant
from aiohttp import web

from .binding_storage import Home3DBindingStorage
from .const import BINDING_CONFIG_VERSION
from .const import FRONTEND_URL_BASE

_LOGGER = logging.getLogger(__name__)
_MAX_MODEL_UPLOAD_BYTES = 50 * 1024 * 1024
_DEFAULT_MODEL_FILE = "casa_demo.glb"


def _frontend_assets_path() -> Path:
    """Return the folder containing frontend assets for Home3D panel."""
    return Path(__file__).resolve().parent / "www"


def _bundled_models_path() -> Path:
    return _frontend_assets_path() / "glb"


def _normalize_model_filename(value: str) -> str:
    filename = Path(str(value).strip()).name
    if not filename or not filename.lower().endswith(".glb"):
        raise ValueError("Only .glb files are supported")
    return filename


class Home3DModelUploadView(HomeAssistantView):
    """HTTP API endpoint for GLB model upload."""

    url = "/api/home3d/upload_model"
    name = "api:home3d:upload_model"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Upload one GLB model using binary request body."""
        request_source = request.remote or "unknown"
        _LOGGER.info("[Home3D][HTTP Upload] step-1 request received from=%s", request_source)

        try:
            filename = _normalize_model_filename(request.query.get("filename", ""))
        except ValueError as err:
            _LOGGER.warning("[Home3D][HTTP Upload] step-2 invalid filename from=%s reason=%s", request_source, err)
            return self.json_message(str(err), status_code=400)

        overwrite = request.query.get("overwrite", "0") in {"1", "true", "True"}
        _LOGGER.info(
            "[Home3D][HTTP Upload] step-2 filename validated filename=%s overwrite=%s",
            filename,
            overwrite,
        )

        try:
            payload = await request.read()
        except Exception as err:  # pragma: no cover
            _LOGGER.warning("Failed to read upload payload", exc_info=True)
            return self.json_message(f"Unable to read upload payload: {err}", status_code=400)

        _LOGGER.info("[Home3D][HTTP Upload] step-3 payload read filename=%s size=%s", filename, len(payload))

        if not payload:
            _LOGGER.warning("[Home3D][HTTP Upload] step-4 payload empty filename=%s", filename)
            return self.json_message("Model payload is empty", status_code=400)

        if len(payload) > _MAX_MODEL_UPLOAD_BYTES:
            _LOGGER.warning(
                "[Home3D][HTTP Upload] step-4 payload too large filename=%s size=%s max=%s",
                filename,
                len(payload),
                _MAX_MODEL_UPLOAD_BYTES,
            )
            return self.json_message(
                f"Model is too large. Maximum size is {_MAX_MODEL_UPLOAD_BYTES // (1024 * 1024)}MB",
                status_code=413,
            )

        models_path = _bundled_models_path()
        _LOGGER.info("[Home3D][HTTP Upload] step-5 ensuring model dir path=%s", models_path)
        try:
            await self._hass.async_add_executor_job(lambda: models_path.mkdir(parents=True, exist_ok=True))
        except OSError as err:
            _LOGGER.exception("[Home3D][HTTP Upload] step-5 failed creating dir path=%s", models_path)
            return self.json_message(f"Unable to create model directory: {err}", status_code=500)

        output_path = models_path / filename
        if output_path.exists() and not overwrite:
            _LOGGER.warning(
                "[Home3D][HTTP Upload] step-6 target exists and overwrite disabled path=%s",
                output_path,
            )
            return self.json_message("Model already exists", status_code=409)

        _LOGGER.info("[Home3D][HTTP Upload] step-6 writing file path=%s", output_path)
        try:
            await self._hass.async_add_executor_job(output_path.write_bytes, payload)
        except OSError as err:
            _LOGGER.exception("[Home3D][HTTP Upload] step-6 failed writing file path=%s", output_path)
            return self.json_message(f"Unable to save model: {err}", status_code=500)

        _LOGGER.info(
            "[Home3D][HTTP Upload] step-7 completed successfully filename=%s size=%s",
            filename,
            len(payload),
        )
        return self.json({"filename": filename, "size": len(payload)})


class Home3DBindingImportView(HomeAssistantView):
    """HTTP API endpoint for importing full binding config payload."""

    url = "/api/home3d/import_bindings"
    name = "api:home3d:import_bindings"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Import full bindings document over HTTP to bypass websocket payload limits."""
        _LOGGER.info("[Home3D][BackupImport] step-1 request received")

        try:
            payload = await request.json()
        except Exception as err:  # pragma: no cover
            _LOGGER.warning("[Home3D][BackupImport] step-2 invalid json payload reason=%s", err)
            return self.json_message(f"Invalid JSON payload: {err}", status_code=400)

        if not isinstance(payload, dict):
            _LOGGER.warning("[Home3D][BackupImport] step-2 payload is not object")
            return self.json_message("Payload must be an object", status_code=400)

        config: dict[str, Any]
        model_bindings = payload.get("model_bindings")
        if isinstance(model_bindings, dict):
            config = {
                "version": 2,
                "model_bindings": model_bindings,
            }
        else:
            version = payload.get("version")
            bindings = payload.get("bindings")
            if not isinstance(version, int) or not isinstance(bindings, dict):
                _LOGGER.warning(
                    "[Home3D][BackupImport] step-2 invalid schema version_type=%s bindings_type=%s model_bindings_type=%s",
                    type(version).__name__,
                    type(bindings).__name__,
                    type(model_bindings).__name__,
                )
                return self.json_message("Invalid binding document schema", status_code=400)

            config = {
                "version": 2,
                "model_bindings": {
                    _DEFAULT_MODEL_FILE: {
                        "version": version if version > 0 else BINDING_CONFIG_VERSION,
                        "bindings": bindings,
                    }
                },
            }

        imported_model_bindings = config.get("model_bindings", {})
        imported_model_count = len(imported_model_bindings) if isinstance(imported_model_bindings, dict) else 0
        imported_binding_count = 0
        if isinstance(imported_model_bindings, dict):
            for model_config in imported_model_bindings.values():
                if isinstance(model_config, dict) and isinstance(model_config.get("bindings"), dict):
                    imported_binding_count += len(model_config["bindings"])

        _LOGGER.info(
            "[Home3D][BackupImport] step-3 persisting models=%s bindings_count=%s",
            imported_model_count,
            imported_binding_count,
        )
        try:
            storage = Home3DBindingStorage(self._hass)
            await storage.async_save(config)
        except Exception as err:  # pragma: no cover
            _LOGGER.exception("[Home3D][BackupImport] step-3 failed to persist")
            return self.json_message(f"Unable to save binding config: {err}", status_code=500)

        _LOGGER.info(
            "[Home3D][BackupImport] step-4 completed successfully version=%s models=%s bindings_count=%s",
            config["version"],
            imported_model_count,
            imported_binding_count,
        )
        return self.json(
            {
                "version": config["version"],
                "models_count": imported_model_count,
                "bindings_count": imported_binding_count,
            }
        )

async def async_setup_frontend_resources(hass: HomeAssistant) -> None:
    """Register static resources used by Home3D frontend panel."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL_BASE,
                str(_frontend_assets_path()),
                cache_headers=False,
            )
        ]
    )
    hass.http.register_view(Home3DModelUploadView(hass))
    hass.http.register_view(Home3DBindingImportView(hass))
