# ==========================================================
# CONFIG.PY
# CONFIGURACIÓN GENERAL - VOLCAN APP
# ==========================================================

APP_NAME = "VOLCAN - Sistema de Gestión de Bombeo"
LOGIN_TITLE = "MANTENIMIENTO VOLCAN"

LOGO_PATH = "assets/logo_volcan.png"
BACKGROUND_PATH = "assets/fondo_login.jpg"

SPREADSHEET_NAME = "VOLCAN_MANTENIMIENTO_DB"

SHEET_USUARIOS = "usuarios"
SHEET_EQUIPOS = "equipos_bombeo"
SHEET_BITACORA = "bitacora"
SHEET_FALLAS = "catalogo_fallas"
SHEET_TRACKLESS = "trackless"

# ==========================================
# NUEVO LUCARBAL
# ==========================================

SHEET_EQUIPOS_LUCARBAL = "equipos_lucarbal"
SHEET_LUCARBAL_EVENTOS = "lucarbal_eventos"

# ==========================================

DRIVE_FOLDER_ID = "1SQm4DWE9R7G0BgraPnYg-sELCCw7edC2"

ROLES = {
    "ADMIN": "Supervisor de Mantenimiento",
    "PLANNER": "Planeamiento / Practicante",
    "TECNICO": "Técnico Mecánico"
}

ESTADOS = [
    "SUBSANADO",
    "PENDIENTE",
    "FUERA DE SERVICIO",
    "EN SEGUIMIENTO"
]

ESTADOS_LUCARBAL = [
    "OPERATIVO",
    "INOPERATIVO",
    "STAND BY"
]

TIPOS_MANTENIMIENTO = [
    "PREVENTIVO",
    "CORRECTIVO"
]

SISTEMAS = [
    "BOMBEO"
]

PAGE_TITLE = "VOLCAN APP"
PAGE_ICON = "⚙️"
LAYOUT = "wide"

COLOR_PRIMARIO = "#D32F2F"
COLOR_SECUNDARIO = "#212121"
COLOR_EXITO = "#2E7D32"
COLOR_ALERTA = "#F57C00"
COLOR_ERROR = "#C62828"
