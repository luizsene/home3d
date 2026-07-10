"""WebSocket commands for Home3D binding editor."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hmac
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .binding_storage import Home3DBindingStorage
from .const import (
    CONF_ADMIN_PASSWORD,
    DOMAIN,
    WS_CMD_DELETE_MODEL,
    WS_CMD_DELETE_BINDING,
    WS_CMD_GET_BINDING_CONFIG,
    WS_CMD_LOAD_BINDINGS,
    WS_CMD_LIST_MODELS,
    WS_CMD_SAVE_BINDINGS,
    WS_CMD_SAVE_BINDING_CONFIG,
    WS_CMD_UPLOAD_MODEL,
    WS_CMD_UPLOAD_MODEL_CHUNK_APPEND,
    WS_CMD_UPLOAD_MODEL_CHUNK_COMMIT,
    WS_CMD_UPLOAD_MODEL_CHUNK_INIT,
    WS_CMD_VERIFY_ADMIN_PASSWORD,
    WS_CMD_UPDATE_BINDING,
)

_BINDING_STORAGE_KEY = f"{DOMAIN}.binding_storage"
_UPLOAD_SESSIONS_KEY = f"{DOMAIN}.upload_sessions"
_LOGGER = logging.getLogger(__name__)
_MAX_MODEL_UPLOAD_BYTES = 50 * 1024 * 1024
_PROTECTED_MODEL_FILENAMES = {"casa.glb", "casa_demo.glb"}
_DEFAULT_MODEL_FILE = "casa_demo.glb"


class ModelUploadError(Exception):
    """Expected model upload failure with explicit websocket error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


async def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Register Home3D websocket commands."""
    if _BINDING_STORAGE_KEY not in hass.data:
        hass.data[_BINDING_STORAGE_KEY] = Home3DBindingStorage(hass)
    if _UPLOAD_SESSIONS_KEY not in hass.data:
        hass.data[_UPLOAD_SESSIONS_KEY] = {}

    websocket_api.async_register_command(hass, ws_get_binding_config)
    websocket_api.async_register_command(hass, ws_save_binding_config)
    websocket_api.async_register_command(hass, ws_load_bindings)
    websocket_api.async_register_command(hass, ws_save_bindings)
    websocket_api.async_register_command(hass, ws_update_binding)
    websocket_api.async_register_command(hass, ws_delete_binding)
    websocket_api.async_register_command(hass, ws_verify_admin_password)
    websocket_api.async_register_command(hass, ws_list_models)
    websocket_api.async_register_command(hass, ws_delete_model)
    websocket_api.async_register_command(hass, ws_upload_model)
    websocket_api.async_register_command(hass, ws_upload_model_chunk_init)
    websocket_api.async_register_command(hass, ws_upload_model_chunk_append)
    websocket_api.async_register_command(hass, ws_upload_model_chunk_commit)


def _get_storage(hass: HomeAssistant) -> Home3DBindingStorage:
    return hass.data[_BINDING_STORAGE_KEY]


def _get_upload_sessions(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    return hass.data[_UPLOAD_SESSIONS_KEY]


def _get_admin_password(hass: HomeAssistant) -> str:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return ""

    value = entries[0].options.get(CONF_ADMIN_PASSWORD, "")
    return str(value).strip() if value is not None else ""


def _get_models_path() -> Path:
    return Path(__file__).resolve().parent / "www" / "glb"


def _get_user_models_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("www")) / "home3d" / "models"


def _list_glb_files(source_path: Path) -> list[str]:
    if not source_path.exists() or not source_path.is_dir():
        return []

    return [
        file_path.name
        for file_path in source_path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() == ".glb"
    ]


async def _async_list_glb_files(hass: HomeAssistant, source_path: Path) -> list[str]:
    return await hass.async_add_executor_job(_list_glb_files, source_path)


async def _async_ensure_dir(hass: HomeAssistant, path: Path) -> None:
    await hass.async_add_executor_job(lambda: path.mkdir(parents=True, exist_ok=True))


async def _async_write_bytes(hass: HomeAssistant, path: Path, content: bytes) -> None:
    await hass.async_add_executor_job(path.write_bytes, content)


async def _async_delete_file_if_exists(hass: HomeAssistant, path: Path) -> bool:
    def _delete() -> bool:
        if not path.exists() or not path.is_file():
            return False

        path.unlink()
        return True

    return await hass.async_add_executor_job(_delete)


def _build_model_too_large_message() -> str:
    return f"Model is too large. Maximum size is {_MAX_MODEL_UPLOAD_BYTES // (1024 * 1024)}MB"


async def _persist_model_bytes(
    hass: HomeAssistant,
    filename: str,
    model_bytes: bytes,
    overwrite: bool,
) -> dict[str, Any]:
    if len(model_bytes) == 0:
        raise ModelUploadError("empty_model_payload", "Model payload is empty")

    if len(model_bytes) > _MAX_MODEL_UPLOAD_BYTES:
        raise ModelUploadError("model_too_large", _build_model_too_large_message())

    models_path = _get_models_path()
    model_path = models_path / filename
    _LOGGER.info("[Home3D][WS Upload] step-5 ensuring model dir path=%s", models_path)

    try:
        await _async_ensure_dir(hass, models_path)
    except OSError as err:
        _LOGGER.exception("[Home3D][WS Upload] step-5 failed creating dir path=%s", models_path)
        raise ModelUploadError("model_dir_failed", f"Unable to create model directory: {err}") from err

    if model_path.exists() and not overwrite:
        _LOGGER.warning(
            "[Home3D][WS Upload] step-6 target exists and overwrite disabled path=%s",
            model_path,
        )
        raise ModelUploadError("model_already_exists", "Model already exists")

    _LOGGER.info("[Home3D][WS Upload] step-6 writing file path=%s", model_path)
    try:
        await _async_write_bytes(hass, model_path, model_bytes)
    except OSError as err:
        _LOGGER.exception("[Home3D][WS Upload] step-6 failed writing file path=%s", model_path)
        raise ModelUploadError("model_write_failed", f"Unable to save model: {err}") from err

    legacy_models_path = _get_user_models_path(hass)
    if legacy_models_path != models_path:
        try:
            _LOGGER.info("[Home3D][WS Upload] step-7 mirroring to legacy path=%s", legacy_models_path)
            await _async_ensure_dir(hass, legacy_models_path)
            await _async_write_bytes(hass, legacy_models_path / filename, model_bytes)
        except OSError:
            _LOGGER.warning("Failed to mirror uploaded model to legacy /local path", exc_info=True)

    repo_models_path = Path(__file__).resolve().parents[2] / "apps" / "viewer" / "public" / "models"
    if repo_models_path.exists() and repo_models_path.is_dir():
        try:
            _LOGGER.info("[Home3D][WS Upload] step-8 mirroring to workspace path=%s", repo_models_path)
            await _async_ensure_dir(hass, repo_models_path)
            await _async_write_bytes(hass, repo_models_path / filename, model_bytes)
        except OSError:
            _LOGGER.warning("Failed to persist uploaded model to workspace public/models", exc_info=True)

    _LOGGER.info(
        "[Home3D][WS Upload] step-9 completed successfully filename=%s size=%s",
        filename,
        len(model_bytes),
    )

    return {
        "filename": filename,
        "size": len(model_bytes),
    }


def _normalize_model_filename(value: str) -> str:
    filename = Path(str(value).strip()).name
    if not filename:
        raise ValueError("Invalid filename")

    if not filename.lower().endswith(".glb"):
        raise ValueError("Only .glb files are supported")

    return filename


def _normalize_binding_model_filename(value: Any) -> str:
    filename = Path(str(value or "").strip()).name
    if not filename:
        return _DEFAULT_MODEL_FILE

    return filename


def _apply_binding_entry(config: dict[str, Any], msg: dict[str, Any]) -> dict[str, Any]:
    """Apply one binding payload into a loaded config document."""
    object_id = str(msg["object_id"]).strip().lower()
    bindings = config.setdefault("bindings", {})

    entity_id = msg.get("entity_id")
    entities = msg.get("entities")
    display_name = msg.get("display_name")
    metadata = msg.get("metadata")

    normalized_entities: list[str] = []
    if isinstance(entities, list):
        normalized_entities = [item for item in entities if isinstance(item, str) and item]

    normalized_entity_id = entity_id if isinstance(entity_id, str) and entity_id else None

    if normalized_entity_id is None and not normalized_entities:
        bindings.pop(object_id, None)
    else:
        entry: dict[str, Any] = {
            "metadata": metadata if isinstance(metadata, dict) else {},
        }

        if normalized_entity_id:
            entry["entity_id"] = normalized_entity_id

        if normalized_entities:
            entry["entities"] = normalized_entities

        if isinstance(display_name, str) and display_name:
            entry["display_name"] = display_name

        bindings[object_id] = entry

    config["version"] = 1
    return config


def _select_binding_config(hass: HomeAssistant, all_config: dict[str, Any], msg: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    model_file = _normalize_binding_model_filename(msg.get("model_file"))
    model_bindings = all_config.setdefault("model_bindings", {})
    model_config = model_bindings.get(model_file)
    if not isinstance(model_config, dict):
        model_config = {
            "version": 1,
            "bindings": {},
        }
        model_bindings[model_file] = model_config

    return model_file, model_config


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_GET_BINDING_CONFIG,
        vol.Optional("model_file"): cv.string,
        vol.Optional("include_all", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_get_binding_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return persisted binding configuration."""
    config = await _get_storage(hass).async_load()
    if bool(msg.get("include_all", False)):
        connection.send_result(msg["id"], config)
        return

    _, model_config = _select_binding_config(hass, config, msg)
    connection.send_result(msg["id"], model_config)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_LOAD_BINDINGS,
        vol.Optional("model_file"): cv.string,
        vol.Optional("include_all", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_load_bindings(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Alias command for loading full bindings document."""
    config = await _get_storage(hass).async_load()
    if bool(msg.get("include_all", False)):
        connection.send_result(msg["id"], config)
        return

    _, model_config = _select_binding_config(hass, config, msg)
    connection.send_result(msg["id"], model_config)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_SAVE_BINDINGS,
        vol.Optional("version"): int,
        vol.Optional("bindings"): dict,
        vol.Optional("model_file"): cv.string,
        vol.Optional("model_bindings"): dict,
    }
)
@websocket_api.async_response
async def ws_save_bindings(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist complete bindings document."""
    storage = _get_storage(hass)
    config = await storage.async_load()

    if isinstance(msg.get("model_bindings"), dict):
        config["model_bindings"] = msg["model_bindings"]
        await storage.async_save(config)
        connection.send_result(msg["id"], config)
        return

    if not isinstance(msg.get("bindings"), dict):
        connection.send_error(msg["id"], "invalid_bindings_payload", "bindings payload is required")
        return

    _, model_config = _select_binding_config(hass, config, msg)
    model_config["version"] = int(msg.get("version", 1))
    model_config["bindings"] = msg["bindings"]
    await storage.async_save(config)
    connection.send_result(msg["id"], model_config)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_SAVE_BINDING_CONFIG,
        vol.Required("object_id"): cv.string,
        vol.Optional("model_file"): cv.string,
        vol.Optional("entity_id"): vol.Any(None, cv.string),
        vol.Optional("entities"): [cv.string],
        vol.Optional("display_name"): vol.Any(None, cv.string),
        vol.Optional("metadata"): dict,
    }
)
@websocket_api.async_response
async def ws_save_binding_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save one model-object binding entry and return updated document."""
    storage = _get_storage(hass)

    try:
        config = await storage.async_load()
        _, model_config = _select_binding_config(hass, config, msg)
        model_config = _apply_binding_entry(model_config, msg)
        config.setdefault("model_bindings", {})[_normalize_binding_model_filename(msg.get("model_file"))] = model_config
        await storage.async_save(config)
        connection.send_result(msg["id"], model_config)
    except Exception as err:  # pragma: no cover - defensive runtime logging
        _LOGGER.exception("Failed to save Home3D binding entry")
        connection.send_error(msg["id"], "binding_save_failed", str(err) or "Failed to save binding")


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_UPDATE_BINDING,
        vol.Required("object_id"): cv.string,
        vol.Optional("model_file"): cv.string,
        vol.Optional("entity_id"): vol.Any(None, cv.string),
        vol.Optional("entities"): [cv.string],
        vol.Optional("display_name"): vol.Any(None, cv.string),
        vol.Optional("metadata"): dict,
    }
)
@websocket_api.async_response
async def ws_update_binding(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Update one binding entry (same behavior as save single entry)."""
    storage = _get_storage(hass)

    try:
        config = await storage.async_load()
        _, model_config = _select_binding_config(hass, config, msg)
        model_config = _apply_binding_entry(model_config, msg)
        config.setdefault("model_bindings", {})[_normalize_binding_model_filename(msg.get("model_file"))] = model_config
        await storage.async_save(config)
        connection.send_result(msg["id"], model_config)
    except Exception as err:  # pragma: no cover - defensive runtime logging
        _LOGGER.exception("Failed to update Home3D binding entry")
        connection.send_error(msg["id"], "binding_update_failed", str(err) or "Failed to update binding")


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_DELETE_BINDING,
        vol.Required("object_id"): cv.string,
        vol.Optional("model_file"): cv.string,
    }
)
@websocket_api.async_response
async def ws_delete_binding(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete one binding entry by object id."""
    object_id = str(msg["object_id"]).strip().lower()
    storage = _get_storage(hass)
    config = await storage.async_load()
    model_file, model_config = _select_binding_config(hass, config, msg)
    model_config.setdefault("bindings", {}).pop(object_id, None)
    config.setdefault("model_bindings", {})[model_file] = model_config
    await storage.async_save(config)
    connection.send_result(msg["id"], model_config)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_VERIFY_ADMIN_PASSWORD,
        vol.Required("password"): cv.string,
    }
)
@websocket_api.async_response
async def ws_verify_admin_password(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Verify admin password for enabling protected edit mode."""
    configured_password = _get_admin_password(hass)
    provided_password = str(msg.get("password", ""))

    configured = bool(configured_password)
    valid = configured and hmac.compare_digest(configured_password, provided_password)

    connection.send_result(
        msg["id"],
        {
            "configured": configured,
            "valid": valid,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_LIST_MODELS,
    }
)
@websocket_api.async_response
async def ws_list_models(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List available GLB models from static assets folder."""
    try:
        bundled_models_path = _get_models_path()
        await _async_ensure_dir(hass, bundled_models_path)

        # Source of truth for viewer model list is the bundled panel folder served by /api/home3d/frontend.
        model_names = sorted(
            set(await _async_list_glb_files(hass, bundled_models_path)),
            key=str.lower,
        )
    except OSError as err:
        connection.send_error(msg["id"], "list_models_failed", f"Unable to list models: {err}")
        return

    connection.send_result(
        msg["id"],
        {
            "models": model_names,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_DELETE_MODEL,
        vol.Required("filename"): cv.string,
    }
)
@websocket_api.async_response
async def ws_delete_model(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete one GLB model from known model locations, except demo model."""
    try:
        filename = _normalize_model_filename(msg["filename"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_model_filename", str(err))
        return

    if filename.lower() in _PROTECTED_MODEL_FILENAMES:
        connection.send_error(msg["id"], "demo_model_protected", "Demo model cannot be deleted")
        return

    candidates: list[Path] = [
        _get_models_path() / filename,
        _get_user_models_path(hass) / filename,
        Path(__file__).resolve().parents[2] / "apps" / "viewer" / "public" / "models" / filename,
    ]

    deleted_paths: list[str] = []
    for file_path in candidates:
        try:
            deleted = await _async_delete_file_if_exists(hass, file_path)
        except OSError as err:
            connection.send_error(msg["id"], "model_delete_failed", f"Unable to delete model: {err}")
            return

        if deleted:
            deleted_paths.append(str(file_path))

    if not deleted_paths:
        connection.send_error(msg["id"], "model_not_found", "Model file not found")
        return

    connection.send_result(
        msg["id"],
        {
            "filename": filename,
            "deleted": True,
            "paths": deleted_paths,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_UPLOAD_MODEL,
        vol.Required("filename"): cv.string,
        vol.Required("content_base64"): cv.string,
        vol.Optional("overwrite", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_upload_model(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Upload a GLB model file into static assets folder."""
    _LOGGER.info("[Home3D][WS Upload] step-1 request received")

    try:
        filename = _normalize_model_filename(msg["filename"])
    except ValueError as err:
        _LOGGER.warning("[Home3D][WS Upload] step-2 invalid filename reason=%s", err)
        connection.send_error(msg["id"], "invalid_model_filename", str(err))
        return

    overwrite = bool(msg.get("overwrite", False))
    _LOGGER.info("[Home3D][WS Upload] step-2 filename validated filename=%s overwrite=%s", filename, overwrite)
    raw_content = str(msg.get("content_base64", "")).strip()
    if not raw_content:
        _LOGGER.warning("[Home3D][WS Upload] step-3 empty payload filename=%s", filename)
        connection.send_error(msg["id"], "empty_model_payload", "Model payload is empty")
        return

    try:
        model_bytes = base64.b64decode(raw_content, validate=True)
    except (binascii.Error, ValueError):
        _LOGGER.warning("[Home3D][WS Upload] step-3 invalid base64 filename=%s", filename)
        connection.send_error(msg["id"], "invalid_model_payload", "Invalid base64 payload")
        return

    _LOGGER.info("[Home3D][WS Upload] step-3 payload decoded filename=%s size=%s", filename, len(model_bytes))

    try:
        result = await _persist_model_bytes(hass, filename, model_bytes, overwrite)
    except ModelUploadError as err:
        connection.send_error(msg["id"], err.code, err.message)
        return

    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_UPLOAD_MODEL_CHUNK_INIT,
        vol.Required("upload_id"): cv.string,
        vol.Required("filename"): cv.string,
        vol.Required("total_chunks"): int,
        vol.Optional("overwrite", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_upload_model_chunk_init(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Initialize one chunked websocket upload session."""
    try:
        filename = _normalize_model_filename(msg["filename"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_model_filename", str(err))
        return

    upload_id = str(msg.get("upload_id", "")).strip()
    if not upload_id:
        connection.send_error(msg["id"], "invalid_upload_id", "Upload id is required")
        return

    total_chunks = int(msg.get("total_chunks", 0))
    if total_chunks <= 0:
        connection.send_error(msg["id"], "invalid_total_chunks", "Total chunks must be greater than 0")
        return

    sessions = _get_upload_sessions(hass)
    sessions[upload_id] = {
        "filename": filename,
        "overwrite": bool(msg.get("overwrite", False)),
        "total_chunks": total_chunks,
        "received_chunks": 0,
        "buffer": bytearray(),
    }

    connection.send_result(
        msg["id"],
        {
            "upload_id": upload_id,
            "total_chunks": total_chunks,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_UPLOAD_MODEL_CHUNK_APPEND,
        vol.Required("upload_id"): cv.string,
        vol.Required("chunk_index"): int,
        vol.Required("content_base64"): cv.string,
    }
)
@websocket_api.async_response
async def ws_upload_model_chunk_append(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Append one websocket chunk to an upload session."""
    upload_id = str(msg.get("upload_id", "")).strip()
    sessions = _get_upload_sessions(hass)
    session = sessions.get(upload_id)
    if session is None:
        connection.send_error(msg["id"], "upload_session_not_found", "Upload session not found")
        return

    expected_index = int(session["received_chunks"])
    chunk_index = int(msg.get("chunk_index", -1))
    if chunk_index != expected_index:
        connection.send_error(
            msg["id"],
            "invalid_chunk_index",
            f"Invalid chunk index. Expected {expected_index}, received {chunk_index}",
        )
        return

    raw_content = str(msg.get("content_base64", "")).strip()
    if not raw_content:
        connection.send_error(msg["id"], "empty_model_payload", "Model payload is empty")
        return

    try:
        chunk_bytes = base64.b64decode(raw_content, validate=True)
    except (binascii.Error, ValueError):
        connection.send_error(msg["id"], "invalid_model_payload", "Invalid base64 payload")
        return

    if len(chunk_bytes) == 0:
        connection.send_error(msg["id"], "empty_model_payload", "Model payload is empty")
        return

    buffer = session["buffer"]
    buffer.extend(chunk_bytes)
    if len(buffer) > _MAX_MODEL_UPLOAD_BYTES:
        sessions.pop(upload_id, None)
        connection.send_error(msg["id"], "model_too_large", _build_model_too_large_message())
        return

    session["received_chunks"] = expected_index + 1

    connection.send_result(
        msg["id"],
        {
            "upload_id": upload_id,
            "received_chunks": session["received_chunks"],
            "total_chunks": session["total_chunks"],
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CMD_UPLOAD_MODEL_CHUNK_COMMIT,
        vol.Required("upload_id"): cv.string,
    }
)
@websocket_api.async_response
async def ws_upload_model_chunk_commit(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Finalize chunked websocket upload and persist model file."""
    upload_id = str(msg.get("upload_id", "")).strip()
    sessions = _get_upload_sessions(hass)
    session = sessions.get(upload_id)
    if session is None:
        connection.send_error(msg["id"], "upload_session_not_found", "Upload session not found")
        return

    try:
        total_chunks = int(session["total_chunks"])
        received_chunks = int(session["received_chunks"])
        if received_chunks != total_chunks:
            connection.send_error(
                msg["id"],
                "incomplete_upload",
                f"Upload incomplete. Received {received_chunks} of {total_chunks} chunks",
            )
            return

        filename = str(session["filename"])
        overwrite = bool(session["overwrite"])
        model_bytes = bytes(session["buffer"])
        result = await _persist_model_bytes(hass, filename, model_bytes, overwrite)
        connection.send_result(msg["id"], result)
    except ModelUploadError as err:
        connection.send_error(msg["id"], err.code, err.message)
    finally:
        sessions.pop(upload_id, None)
