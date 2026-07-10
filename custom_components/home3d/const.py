"""Constants for the Home3D integration."""

from typing import Final

DOMAIN: Final = "home3d"
CONF_ADMIN_PASSWORD: Final = "admin_password"
PANEL_NAME: Final = "home3d"
PANEL_TITLE: Final = "Home3D"
PANEL_ICON: Final = "mdi:home-outline"
PANEL_URL: Final = "/home3d"
FRONTEND_URL_BASE: Final = "/api/home3d/frontend"
PANEL_MODULE_FILE: Final = "home3d-panel.js"
PANEL_MODULE_URL: Final = f"{FRONTEND_URL_BASE}/{PANEL_MODULE_FILE}"
PANEL_WEB_COMPONENT_NAME: Final = "home3d-panel"

BINDING_STORAGE_VERSION: Final = 1
BINDING_STORAGE_KEY: Final = f"{DOMAIN}.bindings"
BINDING_CONFIG_VERSION: Final = 1

WS_CMD_GET_BINDING_CONFIG: Final = f"{DOMAIN}/get_binding_config"
WS_CMD_SAVE_BINDING_CONFIG: Final = f"{DOMAIN}/save_binding_config"
WS_CMD_LOAD_BINDINGS: Final = f"{DOMAIN}/load_bindings"
WS_CMD_SAVE_BINDINGS: Final = f"{DOMAIN}/save_bindings"
WS_CMD_UPDATE_BINDING: Final = f"{DOMAIN}/update_binding"
WS_CMD_DELETE_BINDING: Final = f"{DOMAIN}/delete_binding"
WS_CMD_VERIFY_ADMIN_PASSWORD: Final = f"{DOMAIN}/verify_admin_password"
WS_CMD_LIST_MODELS: Final = f"{DOMAIN}/list_models"
WS_CMD_UPLOAD_MODEL: Final = f"{DOMAIN}/upload_model"
WS_CMD_DELETE_MODEL: Final = f"{DOMAIN}/delete_model"
WS_CMD_UPLOAD_MODEL_CHUNK_INIT: Final = f"{DOMAIN}/upload_model_chunk_init"
WS_CMD_UPLOAD_MODEL_CHUNK_APPEND: Final = f"{DOMAIN}/upload_model_chunk_append"
WS_CMD_UPLOAD_MODEL_CHUNK_COMMIT: Final = f"{DOMAIN}/upload_model_chunk_commit"
