# ==========================================================
# DATABASE.PY
# CONEXIÓN GOOGLE SHEETS
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
    SHEET_TRACKLESS
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


def obtener_hojas():

    sheet = conectar_google_sheets()

    hojas = {
        "usuarios": sheet.worksheet(SHEET_USUARIOS),
        "equipos": sheet.worksheet(SHEET_EQUIPOS),
        "bitacora": sheet.worksheet(SHEET_BITACORA),
        "fallas": sheet.worksheet(SHEET_FALLAS),
        "trackless": sheet.worksheet(SHEET_TRACKLESS)
    }

    return hojas


def cargar_usuarios():

    ws = obtener_hojas()["usuarios"]

    return pd.DataFrame(ws.get_all_records())


def cargar_equipos():

    ws = obtener_hojas()["equipos"]

    return pd.DataFrame(ws.get_all_records())


def cargar_bitacora():

    ws = obtener_hojas()["bitacora"]

    return pd.DataFrame(ws.get_all_records())


def cargar_fallas():

    ws = obtener_hojas()["fallas"]

    return pd.DataFrame(ws.get_all_records())


def cargar_trackless():

    ws = obtener_hojas()["trackless"]

    return pd.DataFrame(ws.get_all_records())


def guardar_bitacora(datos):

    ws = obtener_hojas()["bitacora"]

    ws.append_row(
        datos,
        value_input_option="USER_ENTERED"
    )


def guardar_trackless(datos):

    ws = obtener_hojas()["trackless"]

    ws.append_row(
        datos,
        value_input_option="USER_ENTERED"
    )


def generar_id():

    df = cargar_bitacora()

    if df.empty:
        return "EVT-000001"

    return f"EVT-{len(df) + 1:06d}"


def generar_id_trackless():

    df = cargar_trackless()

    if df.empty:
        return "TRK-000001"

    return f"TRK-{len(df) + 1:06d}"
