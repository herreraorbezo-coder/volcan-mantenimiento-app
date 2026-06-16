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


def obtener_base64_limpio(foto_base64):

    if not isinstance(foto_base64, str):
        return None

    foto_base64 = foto_base64.strip()

    if foto_base64 in ["", "SIN FOTO", "nan", "None", "N/D"]:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split("base64,")[1]

    try:
        base64.b64decode(foto_base64)
        return foto_base64
    except Exception:
        return None


def limpiar_texto(valor, defecto=""):

    texto = str(valor).strip()

    if texto in ["", "nan", "None", "N/D"]:
        return defecto

    return html.escape(texto)


def tiene_dato(valor):

    valor = str(valor).strip()

    return valor not in ["", "nan", "None", "N/D"]


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


def color_tipo_registro(tipo_registro):

    tipo = str(tipo_registro).upper().strip()

    if "LIMPIEZA" in tipo:
        return "#00ACC1"

    if "ENGRASE" in tipo:
        return "#F57C00"

    if "PARADA" in tipo:
        return "#C62828"

    if "INTERVENCIÓN" in tipo or "INTERVENCION" in tipo:
        return "#F2B705"

    return "#F2B705"


def linea_info(label, valor):

    if not tiene_dato(valor):
        return ""

    return f"""
    <div class="info-line">
        <span class="info-label">{label}:</span>
        <span class="info-value">{valor}</span>
    </div>
    """


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

        id_evento = limpiar_texto(row.get("id_evento", ""))
        fecha = row["fecha"].strftime("%d/%m/%Y")
        turno = limpiar_texto(row.get("turno", ""))
        tipo_registro = limpiar_texto(row.get("tipo_registro", ""))
        area_txt = limpiar_texto(row.get("area", ""))
        equipo_txt = limpiar_texto(row.get("equipo_punto", ""))
        tipo_intervencion = limpiar_texto(row.get("tipo_intervencion", ""))
        motivo_parada = limpiar_texto(row.get("motivo_parada", ""))
        tipo_lubricante = limpiar_texto(row.get("tipo_lubricante", ""))
        hora_inicio = limpiar_texto(row.get("hora_inicio", ""))
        hora_fin = limpiar_texto(row.get("hora_fin", ""))
        tiempo_parada_min = limpiar_texto(row.get("tiempo_parada_min", ""))
        tecnico = limpiar_texto(row.get("tecnico", ""))
        apoyo = limpiar_texto(row.get("apoyo", ""))
        requiere_repuesto = limpiar_texto(row.get("requiere_repuesto", ""))
        repuesto_requerido = limpiar_texto(row.get("repuesto_requerido", ""))
        detalle = limpiar_texto(row.get("detalle", "Sin detalle registrado."))
        estado_txt = limpiar_texto(row.get("estado", ""))
        foto_base64 = obtener_base64_limpio(row.get("evidencia", ""))

        color = color_estado(estado_txt)
        color_borde = color_tipo_registro(tipo_registro)

        titulo_principal = equipo_txt

        if not tiene_dato(titulo_principal):
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

        info_adicional = ""

        info_adicional += linea_info("Equipo / punto", equipo_txt)
        info_adicional += linea_info("Motivo parada", motivo_parada)
        info_adicional += linea_info("Lubricante", tipo_lubricante)

        if requiere_repuesto.upper() == "SI":
            info_adicional += linea_info(
                "Requiere repuesto/material",
                requiere_repuesto
            )
            info_adicional += linea_info(
                "Repuesto/material requerido",
                repuesto_requerido
            )

        bloque_info_adicional = ""

        if tiene_dato(info_adicional):
            bloque_info_adicional = f"""
            <div class="repo-section-title">Información adicional</div>
            <div class="repo-text">
                {info_adicional}
            </div>
            """

        bloque_apoyo = ""

        if tiene_dato(apoyo):
            bloque_apoyo = f"""
            <div class="footer-chip">
                🤝 Apoyo: <b>{apoyo}</b>
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
                border-left: 7px solid {color_borde};
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
                color: {color_borde};
                font-size: 13px;
                font-weight: 900;
                margin-top: 8px;
                margin-bottom: 4px;
                text-transform: uppercase;
            }}

            .repo-text {{
                color: #eeeeee;
                font-size: 14px;
                line-height: 1.45;
            }}

            .info-line {{
                margin-bottom: 3px;
            }}

            .info-label {{
                color: #ffffff;
                font-weight: 800;
            }}

            .info-value {{
                color: #eeeeee;
                font-weight: 600;
            }}

            .repo-footer {{
                margin-top: 14px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}

            .footer-chip {{
                background: rgba(255,255,255,0.09);
                border: 1px solid rgba(255,255,255,0.12);
                color: #ffffff;
                border-radius: 12px;
                padding: 8px 12px;
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

                    {bloque_info_adicional}

                    <div class="repo-footer">
                        <div class="footer-chip">
                            👨‍🔧 Registrado por: <b>{tecnico}</b>
                        </div>

                        {bloque_apoyo}
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
