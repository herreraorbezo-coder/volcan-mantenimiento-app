# ==========================================================
# DATABASE.PY
# CONEXIÓN GOOGLE SHEETS + EDICIÓN SEGURA DE REGISTROS
# ==========================================================

import unicodedata
from typing import Any, Dict, Iterable, Optional

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

from config import (
    SPREADSHEET_NAME,
    SHEET_USUARIOS,
    SHEET_EQUIPOS,
    SHEET_BITACORA,
    SHEET_FALLAS,
    SHEET_TRACKLESS,
    SHEET_VOLCAN_TALLER,
    SHEET_EQUIPOS_LUCARBAL,
    SHEET_LUCARBAL_EVENTOS,
    SHEET_LUCARBAL_TALLER,
    SHEET_PLANTA_MOVIL_EVENTOS,
    SHEET_DESPACHO_MIXERS,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def conectar_google_sheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["google_credentials"],
        scopes=SCOPES,
    )
    cliente = gspread.authorize(credentials)
    return cliente.open(SPREADSHEET_NAME)


@st.cache_resource
def obtener_hojas():
    sheet = conectar_google_sheets()
    return {
        "usuarios": sheet.worksheet(SHEET_USUARIOS),
        "equipos": sheet.worksheet(SHEET_EQUIPOS),
        "bitacora": sheet.worksheet(SHEET_BITACORA),
        "fallas": sheet.worksheet(SHEET_FALLAS),
        "trackless": sheet.worksheet(SHEET_TRACKLESS),
        "volcan_taller": sheet.worksheet(SHEET_VOLCAN_TALLER),
        "equipos_lucarbal": sheet.worksheet(SHEET_EQUIPOS_LUCARBAL),
        "lucarbal_eventos": sheet.worksheet(SHEET_LUCARBAL_EVENTOS),
        "lucarbal_taller": sheet.worksheet(SHEET_LUCARBAL_TALLER),
        "planta_movil_eventos": sheet.worksheet(SHEET_PLANTA_MOVIL_EVENTOS),
        "despacho_mixers": sheet.worksheet(SHEET_DESPACHO_MIXERS),
    }


# ==========================================================
# CARGA DE DATOS CON CACHE CONTROLADO
# ==========================================================

@st.cache_data(ttl=60)
def cargar_usuarios():
    return pd.DataFrame(obtener_hojas()["usuarios"].get_all_records())


@st.cache_data(ttl=60)
def cargar_equipos():
    return pd.DataFrame(obtener_hojas()["equipos"].get_all_records())


@st.cache_data(ttl=30)
def cargar_bitacora():
    return pd.DataFrame(obtener_hojas()["bitacora"].get_all_records())


@st.cache_data(ttl=60)
def cargar_fallas():
    return pd.DataFrame(obtener_hojas()["fallas"].get_all_records())


@st.cache_data(ttl=30)
def cargar_trackless():
    return pd.DataFrame(obtener_hojas()["trackless"].get_all_records())


@st.cache_data(ttl=30)
def cargar_volcan_taller():
    return pd.DataFrame(obtener_hojas()["volcan_taller"].get_all_records())


@st.cache_data(ttl=60)
def cargar_equipos_lucarbal():
    return pd.DataFrame(obtener_hojas()["equipos_lucarbal"].get_all_records())


@st.cache_data(ttl=30)
def cargar_lucarbal_eventos():
    return pd.DataFrame(obtener_hojas()["lucarbal_eventos"].get_all_records())


@st.cache_data(ttl=30)
def cargar_lucarbal_taller():
    return pd.DataFrame(obtener_hojas()["lucarbal_taller"].get_all_records())


@st.cache_data(ttl=30)
def cargar_planta_movil_eventos():
    return pd.DataFrame(obtener_hojas()["planta_movil_eventos"].get_all_records())


@st.cache_data(ttl=30)
def cargar_despacho_mixers():
    return pd.DataFrame(obtener_hojas()["despacho_mixers"].get_all_records())


# ==========================================================
# GUARDAR DATOS
# ==========================================================

def guardar_bitacora(datos):
    obtener_hojas()["bitacora"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_bitacora.clear()


def guardar_trackless(datos):
    obtener_hojas()["trackless"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_trackless.clear()


def guardar_volcan_taller(datos):
    obtener_hojas()["volcan_taller"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_volcan_taller.clear()


def guardar_lucarbal_evento(datos):
    obtener_hojas()["lucarbal_eventos"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_lucarbal_eventos.clear()


def guardar_lucarbal_taller(datos):
    obtener_hojas()["lucarbal_taller"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_lucarbal_taller.clear()


def guardar_planta_movil_evento(datos):
    obtener_hojas()["planta_movil_eventos"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_planta_movil_eventos.clear()


def guardar_despacho_mixer(datos):
    obtener_hojas()["despacho_mixers"].append_row(datos, value_input_option="USER_ENTERED")
    cargar_despacho_mixers.clear()


# ==========================================================
# EDICIÓN SEGURA POR ID
# ==========================================================

def _normalizar_encabezado(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.strip().lower().replace("_", " ").split())


def _mapa_encabezados(ws) -> Dict[str, int]:
    encabezados = ws.row_values(1)
    return {
        _normalizar_encabezado(nombre): indice
        for indice, nombre in enumerate(encabezados, start=1)
        if str(nombre).strip()
    }


def _asegurar_columnas(ws, columnas: Iterable[str]) -> Dict[str, int]:
    """
    Garantiza que las columnas solicitadas existan en la fila 1.

    Se utiliza update_cell() en lugar de Worksheet.update() para evitar
    incompatibilidades entre versiones de gspread en Streamlit Cloud.
    También amplía la cantidad de columnas físicas de la hoja cuando sea
    necesario.
    """
    encabezados = ws.row_values(1)
    mapa = _mapa_encabezados(ws)

    nuevas = [
        str(columna).strip()
        for columna in columnas
        if str(columna).strip()
        and _normalizar_encabezado(columna) not in mapa
    ]

    if not nuevas:
        return mapa

    inicio = len(encabezados) + 1
    total_requerido = len(encabezados) + len(nuevas)

    # Google Sheets puede tener menos columnas físicas que las requeridas.
    if ws.col_count < total_requerido:
        ws.add_cols(total_requerido - ws.col_count)

    # Escritura individual, compatible con gspread 5.x y 6.x.
    for desplazamiento, nombre_columna in enumerate(nuevas):
        ws.update_cell(1, inicio + desplazamiento, nombre_columna)

    return _mapa_encabezados(ws)


def _buscar_fila_por_id(ws, columna_id: str, registro_id: str) -> Optional[int]:
    mapa = _mapa_encabezados(ws)
    indice_columna = mapa.get(_normalizar_encabezado(columna_id))
    if not indice_columna:
        return None

    valores = ws.col_values(indice_columna)
    objetivo = str(registro_id).strip()

    for numero_fila, valor in enumerate(valores[1:], start=2):
        if str(valor).strip() == objetivo:
            return numero_fila
    return None


def actualizar_registro_por_id(
    clave_hoja: str,
    columna_id: str,
    registro_id: str,
    cambios: Dict[str, Any],
    modificado_por: str = "",
    fecha_modificacion: str = "",
) -> bool:
    """Actualiza solo las columnas indicadas y conserva el resto de la fila."""
    if not registro_id or not cambios:
        return False

    ws = obtener_hojas()[clave_hoja]
    auditoria = {
        "ultima_modificacion": fecha_modificacion,
        "modificado_por": modificado_por,
    }
    cambios_finales = {**cambios, **auditoria}
    mapa = _asegurar_columnas(ws, cambios_finales.keys())
    numero_fila = _buscar_fila_por_id(ws, columna_id, registro_id)

    if numero_fila is None:
        raise ValueError(f"No se encontró el registro {registro_id} en {clave_hoja}.")

    actualizaciones = []
    for columna, valor in cambios_finales.items():
        indice = mapa.get(_normalizar_encabezado(columna))
        if indice:
            actualizaciones.append({
                "range": rowcol_to_a1(numero_fila, indice),
                "values": [["" if valor is None else valor]],
            })

    if not actualizaciones:
        return False

    ws.batch_update(actualizaciones, value_input_option="USER_ENTERED")
    refrescar_cache_datos()
    return True


def actualizar_bitacora(registro_id: str, cambios: Dict[str, Any], modificado_por="", fecha_modificacion=""):
    return actualizar_registro_por_id(
        "bitacora", "id", registro_id, cambios, modificado_por, fecha_modificacion
    )


def actualizar_lucarbal_evento(registro_id: str, cambios: Dict[str, Any], modificado_por="", fecha_modificacion=""):
    return actualizar_registro_por_id(
        "lucarbal_eventos", "id", registro_id, cambios, modificado_por, fecha_modificacion
    )


def actualizar_volcan_taller(registro_id: str, cambios: Dict[str, Any], modificado_por="", fecha_modificacion=""):
    return actualizar_registro_por_id(
        "volcan_taller", "id_taller", registro_id, cambios, modificado_por, fecha_modificacion
    )


def actualizar_lucarbal_taller(registro_id: str, cambios: Dict[str, Any], modificado_por="", fecha_modificacion=""):
    return actualizar_registro_por_id(
        "lucarbal_taller", "id_taller", registro_id, cambios, modificado_por, fecha_modificacion
    )


# ==========================================================
# GENERAR IDS
# ==========================================================

def _generar_id_generico(clave_hoja, cargar_funcion, prefijo):
    try:
        ws = obtener_hojas()[clave_hoja]
        total_filas = max(len(ws.col_values(1)) - 1, 0)
        return f"{prefijo}-{total_filas + 1:06d}"
    except Exception:
        df = cargar_funcion()
        return f"{prefijo}-{len(df) + 1:06d}"


def generar_id():
    return _generar_id_generico("bitacora", cargar_bitacora, "EVT")


def generar_id_trackless():
    return _generar_id_generico("trackless", cargar_trackless, "TRK")


def generar_id_volcan_taller():
    return _generar_id_generico("volcan_taller", cargar_volcan_taller, "VT")


def generar_id_lucarbal():
    return _generar_id_generico("lucarbal_eventos", cargar_lucarbal_eventos, "LUC")


def generar_id_lucarbal_taller():
    return _generar_id_generico("lucarbal_taller", cargar_lucarbal_taller, "TALLER")


def generar_id_planta_movil():
    return _generar_id_generico("planta_movil_eventos", cargar_planta_movil_eventos, "PM")


def generar_id_despacho_mixer():
    return _generar_id_generico("despacho_mixers", cargar_despacho_mixers, "MIX")


# ==========================================================
# REFRESCAR CACHE MANUALMENTE
# ==========================================================

def refrescar_cache_datos():
    funciones_cache = [
        cargar_usuarios,
        cargar_equipos,
        cargar_bitacora,
        cargar_fallas,
        cargar_trackless,
        cargar_volcan_taller,
        cargar_equipos_lucarbal,
        cargar_lucarbal_eventos,
        cargar_lucarbal_taller,
        cargar_planta_movil_eventos,
        cargar_despacho_mixers,
    ]
    for funcion in funciones_cache:
        try:
            funcion.clear()
        except Exception:
            pass
