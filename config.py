# ==========================================================
# CONFIG.PY
# CONFIGURACIÓN GENERAL - VOLCAN APP
# ==========================================================

APP_NAME = "VOLCAN - Sistema de Gestión de Mantenimiento"
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
# VOLCAN - TALLER / APOYOS
# ==========================================

SHEET_VOLCAN_TALLER = "volcan_taller"

# ==========================================
# LUCARBAL
# ==========================================

SHEET_EQUIPOS_LUCARBAL = "equipos_lucarbal"
SHEET_LUCARBAL_EVENTOS = "lucarbal_eventos"
SHEET_LUCARBAL_TALLER = "lucarbal_taller"

# ==========================================
# PLANTA MÓVIL - LIVERH
# ==========================================

SHEET_PLANTA_MOVIL_EVENTOS = "planta_movil_eventos"
SHEET_DESPACHO_MIXERS = "despacho_mixers"

# ==========================================

DRIVE_FOLDER_ID = "1SQm4DWE9R7G0BgraPnYg-sELCCw7edC2"

ROLES = {
    "ADMIN": "Supervisor de Mantenimiento",
    "PLANNER": "Planeamiento / Practicante",
    "TECNICO": "Técnico Mecánico",
    "SUPERVISOR": "Supervisor Contratista"
}

ESTADOS = [
    "SUBSANADO",
    "PENDIENTE",
    "FUERA DE SERVICIO",
    "EN SEGUIMIENTO"
]

ESTADOS_TALLER_VOLCAN = [
    "FINALIZADO",
    "EN PROCESO",
    "PENDIENTE"
]

ESTADOS_LUCARBAL = [
    "OPERATIVO",
    "INOPERATIVO",
    "STAND BY"
]

ESTADOS_PLANTA_MOVIL = [
    "OPERATIVO",
    "OPERATIVO CON OBSERVACIÓN",
    "INOPERATIVO",
    "EN SEGUIMIENTO",
    "PENDIENTE"
]

ESTADOS_DESPACHO_MIXERS = [
    "DESPACHADO",
    "PENDIENTE",
    "ANULADO",
    "CON OBSERVACIÓN"
]

TIPOS_MANTENIMIENTO = [
    "PREVENTIVO",
    "CORRECTIVO"
]

SISTEMAS = [
    "BOMBEO",
    "PLANTA MÓVIL"
]

EMPRESAS_APOYO_VOLCAN = [
    "VOLCAN",
    "TAIR",
    "LUCARBAL",
    "SEPROCAL",
    "LIVERH",
    "MANTENIMIENTO ELÉCTRICO",
    "OTROS"
]

AREAS_APOYO_VOLCAN = [
    "TALLER",
    "MINA",
    "SOLDADURA",
    "FABRICACIÓN",
    "CORTE",
    "MANTENIMIENTO MECÁNICO",
    "MANTENIMIENTO ELÉCTRICO",
    "OTROS"
]

PAGE_TITLE = "VOLCAN APP"
PAGE_ICON = "⚙️"
LAYOUT = "wide"

COLOR_PRIMARIO = "#D32F2F"
COLOR_SECUNDARIO = "#212121"
COLOR_EXITO = "#2E7D32"
COLOR_ALERTA = "#F57C00"
COLOR_ERROR = "#C62828"
