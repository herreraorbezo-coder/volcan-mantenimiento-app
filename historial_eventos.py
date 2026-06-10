# ==========================================================
# HISTORIAL_EVENTOS.PY
# REPOSITORIO VISUAL DE EVENTOS - SISTEMA DE BOMBEO
# ==========================================================

import streamlit as st
import pandas as pd
import base64
import html

import streamlit.components.v1 as components

from database import cargar_bitacora


def obtener_base64_limpio(foto_base64):

    if not isinstance(foto_base64, str):
        return None

    foto_base64 = foto_base64.strip()

    if foto_base64 in ["", "SIN FOTO", "nan", "None"]:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split("base64,")[1]

    try:
        base64.b64decode(foto_base64)
        return foto_base64
    except Exception:
        return None


def limpiar_texto(valor, defecto="N/D"):

    texto = str(valor).strip()

    if texto in ["", "nan", "None"]:
        return defecto

    return html.escape(texto)


def color_estado(estado):

    estado = str(estado).upper().strip()

    if "SUBSANADO" in estado:
        return "#2E7D32"

    if "PENDIENTE" in estado:
        return "#F57C00"

    if "FUERA" in estado:
        return "#C62828"

    if "SEGUIMIENTO" in estado:
        return "#1565C0"

    return "#616161"


def mostrar_historial_eventos():

    st.title("🗂️ Repositorio Visual de Eventos")
    st.caption("Sistema de bombeo · Consulta rápida para cambio de guardia")
    st.markdown("---")

    df = cargar_bitacora()

    if df.empty:
        st.warning("No existen eventos registrados.")
        return

    df.columns = df.columns.str.strip().str.lower()

    columnas_necesarias = [
        "id",
        "fecha",
        "nivel",
        "ubicacion",
        "codigo",
        "hora_falla",
        "hora_subsanada",
        "tipo_mantenimiento",
        "tipo_falla",
        "causa_preliminar",
        "descripcion",
        "estado",
        "tecnico",
        "foto"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.warning("No hay eventos con fecha válida.")
        return

    for col in columnas_necesarias:
        if col != "fecha":
            df[col] = df[col].astype(str).str.strip()

    # ======================================================
    # FILTROS
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        nivel = st.selectbox(
            "Nivel",
            ["TODOS"] + sorted(df["nivel"].dropna().unique().tolist())
        )

    with col2:
        codigo = st.selectbox(
            "Código bomba",
            ["TODOS"] + sorted(df["codigo"].dropna().unique().tolist())
        )

    with col3:
        estado = st.selectbox(
            "Estado",
            ["TODOS"] + sorted(df["estado"].dropna().unique().tolist())
        )

    with col4:
        rango = st.selectbox(
            "Periodo",
            ["Últimos 7 días", "Últimos 15 días", "Últimos 30 días", "Todo"]
        )

    df_filtrado = df.copy()

    if nivel != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel]

    if codigo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["codigo"] == codigo]

    if estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado]

    if rango != "Todo":

        fecha_max = df_filtrado["fecha"].max()

        dias = {
            "Últimos 7 días": 7,
            "Últimos 15 días": 15,
            "Últimos 30 días": 30
        }[rango]

        fecha_min = fecha_max - pd.Timedelta(days=dias - 1)

        df_filtrado = df_filtrado[
            df_filtrado["fecha"] >= fecha_min
        ]

    if df_filtrado.empty:
        st.warning("No hay eventos con los filtros seleccionados.")
        return

    df_filtrado = df_filtrado.sort_values("fecha", ascending=False)

    st.info(
        f"Eventos encontrados: **{len(df_filtrado)}** · "
        "ordenado del más reciente al más antiguo."
    )

    st.markdown("---")

    # ======================================================
    # TARJETAS VISUALES
    # ======================================================

    for _, row in df_filtrado.iterrows():

        evento = limpiar_texto(row.get("id", ""))
        fecha = row["fecha"].strftime("%d/%m/%Y")
        nivel_txt = limpiar_texto(row.get("nivel", ""))
        ubicacion = limpiar_texto(row.get("ubicacion", ""))
        codigo_txt = limpiar_texto(row.get("codigo", ""))
        hora_falla = limpiar_texto(row.get("hora_falla", ""))
        hora_subsanada = limpiar_texto(row.get("hora_subsanada", ""))
        tipo_mantenimiento = limpiar_texto(row.get("tipo_mantenimiento", ""))
        tipo_falla = limpiar_texto(row.get("tipo_falla", ""))
        causa = limpiar_texto(row.get("causa_preliminar", ""))
        descripcion = limpiar_texto(row.get("descripcion", "Sin descripción registrada."))
        estado_txt = limpiar_texto(row.get("estado", ""))
        tecnico = limpiar_texto(row.get("tecnico", ""))
        foto_base64 = obtener_base64_limpio(row.get("foto", ""))

        color = color_estado(estado_txt)

        if foto_base64:
            bloque_imagen = f"""
            <div class="image-box">
                <img src="data:image/jpeg;base64,{foto_base64}">
                <div class="image-caption">{codigo_txt} · {evento}</div>
            </div>
            """
        else:
            bloque_imagen = """
            <div class="no-image">
                📷<br>Sin evidencia
            </div>
            """

        html_card = f"""
        <html>
        <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: transparent;
            }}

            .container {{
                display: grid;
                grid-template-columns: 240px 1fr;
                gap: 18px;
                margin-bottom: 18px;
            }}

            .image-box {{
                background: #121212;
                border-radius: 14px;
                padding: 10px;
                border: 1px solid rgba(255,255,255,0.12);
                box-shadow: 0px 8px 20px rgba(0,0,0,0.35);
                height: 250px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}

            .image-box img {{
                max-width: 220px;
                max-height: 200px;
                object-fit: contain;
                border-radius: 10px;
            }}

            .image-caption {{
                color: #d0d0d0;
                font-size: 12px;
                margin-top: 8px;
                text-align: center;
            }}

            .no-image {{
                background: #202020;
                border: 1px dashed #616161;
                border-radius: 14px;
                height: 250px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #9e9e9e;
                font-weight: 700;
                text-align: center;
            }}

            .repo-card {{
                background: linear-gradient(135deg, #1d1d1d 0%, #2a2a2a 100%);
                border-radius: 16px;
                padding: 16px 18px;
                border-left: 7px solid #F2B705;
                box-shadow: 0px 10px 28px rgba(0,0,0,0.35);
                min-height: 220px;
            }}

            .repo-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }}

            .repo-equipo {{
                font-size: 28px;
                font-weight: 900;
                color: #ffffff;
                letter-spacing: 0.5px;
            }}

            .repo-subtitle {{
                color: #bdbdbd;
                font-size: 13px;
                margin-top: 2px;
                margin-bottom: 12px;
            }}

            .repo-estado {{
                color: white;
                padding: 7px 14px;
                border-radius: 20px;
                font-weight: 800;
                font-size: 13px;
                text-align: center;
                min-width: 110px;
            }}

            .repo-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-top: 12px;
                margin-bottom: 14px;
            }}

            .repo-box {{
                background: rgba(255,255,255,0.07);
                border-radius: 10px;
                padding: 10px;
            }}

            .repo-label {{
                color: #9e9e9e;
                font-size: 11px;
                font-weight: 700;
                margin-bottom: 3px;
                text-transform: uppercase;
            }}

            .repo-value {{
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
            }}

            .repo-section-title {{
                color: #F2B705;
                font-size: 13px;
                font-weight: 900;
                margin-top: 8px;
                margin-bottom: 4px;
                text-transform: uppercase;
            }}

            .repo-text {{
                color: #eeeeee;
                font-size: 14px;
                line-height: 1.42;
            }}

            .repo-footer {{
                margin-top: 12px;
                color: #bdbdbd;
                font-size: 12px;
            }}
        </style>
        </head>

        <body>
            <div class="container">
                {bloque_imagen}

                <div class="repo-card">
                    <div class="repo-header">
                        <div>
                            <div class="repo-equipo">{codigo_txt}</div>
                            <div class="repo-subtitle">
                                {evento} · {fecha} · {nivel_txt} · {ubicacion}
                            </div>
                        </div>

                        <div class="repo-estado" style="background:{color};">
                            {estado_txt}
                        </div>
                    </div>

                    <div class="repo-grid">
                        <div class="repo-box">
                            <div class="repo-label">Inicio</div>
                            <div class="repo-value">{hora_falla}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Fin</div>
                            <div class="repo-value">{hora_subsanada}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Mantenimiento</div>
                            <div class="repo-value">{tipo_mantenimiento}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Nivel</div>
                            <div class="repo-value">{nivel_txt}</div>
                        </div>
                    </div>

                    <div class="repo-section-title">Trabajo realizado</div>
                    <div class="repo-text">{descripcion}</div>

                    <div class="repo-section-title">Falla / intervención</div>
                    <div class="repo-text">{tipo_falla}</div>

                    <div class="repo-section-title">Causa preliminar</div>
                    <div class="repo-text">{causa}</div>

                    <div class="repo-footer">
                        Registrado por: <b>{tecnico}</b>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        components.html(
            html_card,
            height=310,
            scrolling=False
        )
