#==========================================================
# DATABASE.PY
# CONEXIÓN GOOGLE SHEETS
# OPTIMIZADO PARA EVITAR ERROR 429
# ==========================================================

import streamlit as st
import gspread
import pandas as pd

from google.oauth2.service_account import Credentials

from config import (
    SPREADSHEET_NAME,
    SHEET_USUARIOS,
    SHEET_EQUIPOS,
    SHEET_BITACORA,
    SHEET_FALLAS,
    SHEET_TRACKLESS,
    SHEET_EQUIPOS_LUCARBAL,
    SHEET_LUCARBAL_EVENTOS
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


@st.cache_resource
def conectar_google_sheets():

    credentials = Credentials.from_service_account_info(
        st.secrets["google_credentials"],
        scopes=SCOPES
    )

    cliente = gspread.authorize(credentials)
    spreadsheet = cliente.open(SPREADSHEET_NAME)

    return spreadsheet


@st.cache_resource
def obtener_hojas():

    sheet = conectar_google_sheets()

    return {
        "usuarios": sheet.worksheet(SHEET_USUARIOS),
        "equipos": sheet.worksheet(SHEET_EQUIPOS),
        "bitacora": sheet.worksheet(SHEET_BITACORA),
        "fallas": sheet.worksheet(SHEET_FALLAS),
        "trackless": sheet.worksheet(SHEET_TRACKLESS),
        "equipos_lucarbal": sheet.worksheet(SHEET_EQUIPOS_LUCARBAL),
        "lucarbal_eventos": sheet.worksheet(SHEET_LUCARBAL_EVENTOS)
    }


# ==========================================================
# CARGA DE DATOS CON CACHE CONTROLADO
# ==========================================================

@st.cache_data(ttl=60)
def cargar_usuarios():
    ws = obtener_hojas()["usuarios"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=60)
def cargar_equipos():
    ws = obtener_hojas()["equipos"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=30)
def cargar_bitacora():
    ws = obtener_hojas()["bitacora"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=60)
def cargar_fallas():
    ws = obtener_hojas()["fallas"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=30)
def cargar_trackless():
    ws = obtener_hojas()["trackless"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=60)
def cargar_equipos_lucarbal():
    ws = obtener_hojas()["equipos_lucarbal"]
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=30)
def cargar_lucarbal_eventos():
    ws = obtener_hojas()["lucarbal_eventos"]
    return pd.DataFrame(ws.get_all_records())


# ==========================================================
# GUARDAR DATOS
# ==========================================================

def guardar_bitacora(datos):
    ws = obtener_hojas()["bitacora"]
    ws.append_row(datos, value_input_option="USER_ENTERED")
    cargar_bitacora.clear()


def guardar_trackless(datos):
    ws = obtener_hojas()["trackless"]
    ws.append_row(datos, value_input_option="USER_ENTERED")
    cargar_trackless.clear()


def guardar_lucarbal_evento(datos):
    ws = obtener_hojas()["lucarbal_eventos"]
    ws.append_row(datos, value_input_option="USER_ENTERED")
    cargar_lucarbal_eventos.clear()


# ==========================================================
# GENERAR IDS
# ==========================================================

def generar_id():

    try:
        ws = obtener_hojas()["bitacora"]
        total_filas = len(ws.col_values(1)) - 1
        return f"EVT-{total_filas + 1:06d}"

    except Exception:
        df = cargar_bitacora()

        if df.empty:
            return "EVT-000001"

        return f"EVT-{len(df) + 1:06d}"


def generar_id_trackless():

    try:
        ws = obtener_hojas()["trackless"]
        total_filas = len(ws.col_values(1)) - 1
        return f"TRK-{total_filas + 1:06d}"

    except Exception:
        df = cargar_trackless()

        if df.empty:
            return "TRK-000001"

        return f"TRK-{len(df) + 1:06d}"


def generar_id_lucarbal():

    try:
        ws = obtener_hojas()["lucarbal_eventos"]
        total_filas = len(ws.col_values(1)) - 1
        return f"LUC-{total_filas + 1:06d}"

    except Exception:
        df = cargar_lucarbal_eventos()

        if df.empty:
            return "LUC-000001"

        return f"LUC-{len(df) + 1:06d}"


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
        cargar_equipos_lucarbal,
        cargar_lucarbal_eventos
    ]

    for funcion in funciones_cache:

        try:
            funcion.clear()

        except Exception:
            pass
