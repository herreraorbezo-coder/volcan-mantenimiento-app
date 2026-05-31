# ==========================================================
# EQUIPOS.PY
# SISTEMA DE BOMBEO VOLCAN
# ==========================================================

import streamlit as st
from database import cargar_equipos


# ==========================================================
# SELECCIÓN BOMBAS
# ==========================================================

def seleccionar_bomba():

    df = cargar_equipos()

    # ==========================================
    # VALIDAR DATAFRAME
    # ==========================================

    if df.empty:

        st.error(
            "No hay equipos cargados en Google Sheets"
        )

        return None

    # ==========================================
    # NORMALIZAR COLUMNAS
    # ==========================================

    df.columns = [
        str(col).strip().lower()
        for col in df.columns
    ]

    # ==========================================
    # NORMALIZAR DATOS
    # ==========================================

    for col in [
        "sistema",
        "nivel",
        "ubicacion",
        "codigo"
    ]:

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
        )

    # ==========================================
    # SISTEMA
    # ==========================================

    sistema = st.selectbox(
        "Sistema",
        ["BOMBEO"]
    )

    # ==========================================
    # NIVEL
    # ==========================================

    niveles = sorted(
        df["nivel"]
        .dropna()
        .unique()
        .tolist()
    )

    nivel = st.selectbox(
        "Nivel",
        niveles
    )

    # ==========================================
    # FILTRAR NIVEL
    # ==========================================

    df_nivel = df[
        df["nivel"] == nivel
    ]

    # ==========================================
    # UBICACIONES
    # ==========================================

    ubicaciones = sorted(
        df_nivel["ubicacion"]
        .dropna()
        .unique()
        .tolist()
    )

    ubicacion = st.selectbox(
        "Ubicación",
        ubicaciones
    )

    # ==========================================
    # OBTENER CÓDIGO
    # ==========================================

    fila = df_nivel[
        df_nivel["ubicacion"]
        == ubicacion
    ]

    if not fila.empty:

        codigo = fila.iloc[0]["codigo"]

    else:

        codigo = "NO ENCONTRADO"

    # ==========================================
    # MOSTRAR CÓDIGO
    # ==========================================

    st.text_input(
        "Código de bomba",
        value=codigo,
        disabled=True
    )

    # ==========================================
    # RETORNAR DATOS
    # ==========================================

    return {
        "sistema": sistema,
        "nivel": nivel,
        "ubicacion": ubicacion,
        "codigo": codigo
    }