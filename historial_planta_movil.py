# ==========================================================
# HISTORIAL_PLANTA_MOVIL.PY
# REPOSITORIO VISUAL DE EVENTOS - PLANTA MÓVIL
# ==========================================================

import streamlit as st
import pandas as pd
import base64
import html

import streamlit.components.v1 as components

from database import cargar_planta_movil_eventos


# ==========================================================
# LIMPIAR FOTO BASE64
# ==========================================================

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


# ==========================================================
# LIMPIAR TEXTO
# ==========================================================

def limpiar_texto(valor, defecto="N/D"):

    texto = str(valor).strip()

    if texto in ["", "nan", "None"]:
        return defecto

    return html.escape(texto)


# ==========================================================
# COLOR POR ESTADO
# ==========================================================

def color_estado(estado):

    estado = str(estado).upper().strip()

    if "OPERATIVO" in estado and "OBSERVACIÓN" not in estado:
        return "#2E7D32"

    if "OBSERVACIÓN" in estado:
        return "#F57C00"

    if "INOPERATIVO" in estado:
        return "#C62828"

    if "SEGUIMIENTO" in estado:
        return "#1565C0"

    if "PENDIENTE" in estado:
        return "#F57C00"

    return "#616161"


# ==========================================================
# MOSTRAR HISTORIAL
# ==========================================================

def mostrar_historial_planta_movil():

    st.title("🗂️ Historial de Mantenimiento - Planta Móvil")
    st.caption(
        "LIVERH · Repositorio visual de intervenciones, limpiezas, engrases, paradas y evidencias"
    )
    st.markdown("---")

    df = cargar_planta_movil_eventos()

    if df.empty:
        st.warning("No existen registros de mantenimiento de Planta Móvil.")
        return

    df.columns = df.columns.str.strip().str.lower()

    columnas_necesarias = [
        "fecha",
        "turno",
        "tipo_registro",
        "area",
        "equipo_punto",
        "tipo_intervencion",
        "motivo_parada",
        "tipo_lubricante",
        "hora_inicio",
        "hora_fin",
        "tiempo_parada_min",
        "tecnico",
        "apoyo",
        "requiere_repuesto",
        "repuesto_requerido",
        "detalle",
        "estado",
        "evidencia",
        "id_evento"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    df["fecha"] = pd.to_datetime(
        df["fecha"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["fecha"]
    )

    if df.empty:
        st.warning("No hay registros con fecha válida.")
        return

    for col in columnas_necesarias:
        if col != "fecha":
            df[col] = df[col].astype(str).str.strip()

    # ======================================================
    # FILTROS
    # ======================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        tipo_registro_filtro = st.selectbox(
            "Tipo registro",
            ["TODOS"] + sorted(
                df["tipo_registro"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col2:

        area = st.selectbox(
            "Área",
            ["TODOS"] + sorted(
                df["area"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col3:

        equipo = st.selectbox(
            "Equipo / punto",
            ["TODOS"] + sorted(
                df["equipo_punto"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col4:

        estado = st.selectbox(
            "Estado",
            ["TODOS"] + sorted(
                df["estado"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col5:

        rango = st.selectbox(
            "Periodo",
            [
                "Últimos 7 días",
                "Últimos 15 días",
                "Últimos 30 días",
                "Todo"
            ]
        )

    df_filtrado = df.copy()

    if tipo_registro_filtro != "TODOS":
        df_filtrado = df_filtrado[
            df_filtrado["tipo_registro"] == tipo_registro_filtro
        ]

    if area != "TODOS":
        df_filtrado = df_filtrado[
            df_filtrado["area"] == area
        ]

    if equipo != "TODOS":
        df_filtrado = df_filtrado[
            df_filtrado["equipo_punto"] == equipo
        ]

    if estado != "TODOS":
        df_filtrado = df_filtrado[
            df_filtrado["estado"] == estado
        ]

    if rango != "Todo":

        fecha_max = df_filtrado["fecha"].max()

        dias = {
            "Últimos 7 días": 7,
            "Últimos 15 días": 15,
            "Últimos 30 días": 30
        }[rango]

        fecha_min = fecha_max - pd.Timedelta(
            days=dias - 1
        )

        df_filtrado = df_filtrado[
            df_filtrado["fecha"] >= fecha_min
        ]

    if df_filtrado.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

    df_filtrado = df_filtrado.sort_values(
        "fecha",
        ascending=False
    )

    st.info(
        f"Registros encontrados: **{len(df_filtrado)}** · "
        "ordenado del más reciente al más antiguo."
    )

    st.markdown("---")

    # ======================================================
    # TARJETAS VISUALES
    # ======================================================

    for _, row in df_filtrado.iterrows():

        id_evento = limpiar_texto(
            row.get("id_evento", "")
        )

        fecha = row["fecha"].strftime("%d/%m/%Y")

        turno = limpiar_texto(
            row.get("turno", "")
        )

        tipo_registro = limpiar_texto(
            row.get("tipo_registro", "")
        )

        area_txt = limpiar_texto(
            row.get("area", "")
        )

        equipo_txt = limpiar_texto(
            row.get("equipo_punto", "")
        )

        tipo_intervencion = limpiar_texto(
            row.get("tipo_intervencion", "")
        )

        motivo_parada = limpiar_texto(
            row.get("motivo_parada", "")
        )

        tipo_lubricante = limpiar_texto(
            row.get("tipo_lubricante", "")
        )

        hora_inicio = limpiar_texto(
            row.get("hora_inicio", "")
        )

        hora_fin = limpiar_texto(
            row.get("hora_fin", "")
        )

        tiempo_parada_min = limpiar_texto(
            row.get("tiempo_parada_min", "0")
        )

        tecnico = limpiar_texto(
            row.get("tecnico", "")
        )

        apoyo = limpiar_texto(
            row.get("apoyo", "")
        )

        requiere_repuesto = limpiar_texto(
            row.get("requiere_repuesto", "NO")
        )

        repuesto_requerido = limpiar_texto(
            row.get("repuesto_requerido", "NINGUNO")
        )

        detalle = limpiar_texto(
            row.get("detalle", "Sin detalle registrado.")
        )

        estado_txt = limpiar_texto(
            row.get("estado", "")
        )

        foto_base64 = obtener_base64_limpio(
            row.get("evidencia", "")
        )

        color = color_estado(
            estado_txt
        )

        titulo_principal = equipo_txt

        if equipo_txt in ["", "N/D"]:
            titulo_principal = tipo_registro

        if foto_base64:

            bloque_imagen = f"""
            <div class="image-box">
                <img src="data:image/jpeg;base64,{foto_base64}">
                <div class="image-caption">{titulo_principal} · {id_evento}</div>
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
                height: 290px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}

            .image-box img {{
                max-width: 220px;
                max-height: 235px;
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
                height: 290px;
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
                min-height: 260px;
            }}

            .repo-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }}

            .repo-equipo {{
                font-size: 26px;
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
                min-width: 120px;
            }}

            .repo-grid {{
                display: grid;
                grid-template-columns: repeat(6, 1fr);
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

            .repo-alert {{
                margin-top: 8px;
                background: rgba(245, 124, 0, 0.18);
                border-left: 4px solid #F57C00;
                padding: 8px 10px;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }}
        </style>
        </head>

        <body>
            <div class="container">
                {bloque_imagen}

                <div class="repo-card">
                    <div class="repo-header">
                        <div>
                            <div class="repo-equipo">{titulo_principal}</div>
                            <div class="repo-subtitle">
                                {id_evento} · {fecha} · {turno} · {area_txt}
                            </div>
                        </div>

                        <div class="repo-estado" style="background:{color};">
                            {estado_txt}
                        </div>
                    </div>

                    <div class="repo-grid">
                        <div class="repo-box">
                            <div class="repo-label">Inicio</div>
                            <div class="repo-value">{hora_inicio}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Fin</div>
                            <div class="repo-value">{hora_fin}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Tiempo</div>
                            <div class="repo-value">{tiempo_parada_min} min</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Intervención</div>
                            <div class="repo-value">{tipo_intervencion}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Turno</div>
                            <div class="repo-value">{turno}</div>
                        </div>

                        <div class="repo-box">
                            <div class="repo-label">Registro</div>
                            <div class="repo-value">{tipo_registro}</div>
                        </div>
                    </div>

                    <div class="repo-section-title">Detalle técnico</div>
                    <div class="repo-text">{detalle}</div>

                    <div class="repo-section-title">Información adicional</div>
                    <div class="repo-text">
                        <b>Equipo / punto:</b> {equipo_txt}<br>
                        <b>Motivo parada:</b> {motivo_parada}<br>
                        <b>Lubricante:</b> {tipo_lubricante}<br>
                        <b>Requiere repuesto/material:</b> {requiere_repuesto}<br>
                        <b>Repuesto/material requerido:</b> {repuesto_requerido}
                    </div>

                    <div class="repo-footer">
                        Registrado por: <b>{tecnico}</b> · Apoyo: <b>{apoyo}</b>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        components.html(
            html_card,
            height=365,
            scrolling=False
        )
