# ==========================================================
# HISTORIAL_DESPACHO_MIXERS.PY
# REPOSITORIO VISUAL - DESPACHO MIXERS
# ==========================================================

import streamlit as st
import pandas as pd
import base64
import html

import streamlit.components.v1 as components

from database import cargar_despacho_mixers


def obtener_base64_limpio(foto_base64):

    if not isinstance(foto_base64, str):
        return None

    foto_base64 = foto_base64.strip()

    if foto_base64 in [
        "",
        "SIN FOTO",
        "nan",
        "None"
    ]:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split(
            "base64,"
        )[1]

    try:
        base64.b64decode(
            foto_base64
        )

        return foto_base64

    except Exception:
        return None


def limpiar_texto(
    valor,
    defecto="N/D"
):

    texto = str(valor).strip()

    if texto in [
        "",
        "nan",
        "None"
    ]:
        return defecto

    return html.escape(texto)


def color_estado(estado):

    estado = str(
        estado
    ).upper().strip()

    if "DESPACHADO" in estado:
        return "#2E7D32"

    if "OBSERVACIÓN" in estado:
        return "#F57C00"

    if "PENDIENTE" in estado:
        return "#1565C0"

    if "ANULADO" in estado:
        return "#C62828"

    return "#616161"


def mostrar_historial_despacho_mixers():

    st.title(
        "🚚 Historial Despacho Mixers"
    )

    st.caption(
        "LIVERH · Repositorio visual de atención de mixers"
    )

    st.markdown("---")

    df = cargar_despacho_mixers()

    if df.empty:

        st.warning(
            "No existen registros de despacho."
        )

        return

    df.columns = (

        df.columns
        .str.strip()
        .str.lower()

    )

    columnas_necesarias = [

        "id_despacho",
        "fecha",
        "turno",
        "supervisor",
        "mixer",
        "codigo_cognos",
        "hora_llegada",
        "hora_inicio_carga",
        "hora_salida",
        "tiempo_espera_min",
        "tiempo_total_min",
        "metros_cubicos",
        "causa_espera",
        "detalle",
        "estado",
        "evidencia"
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

        st.warning(
            "No hay registros con fecha válida."
        )

        return

    # ======================================================
    # FILTROS
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        mixer = st.selectbox(
            "Mixer",
            ["TODOS"]
            + sorted(
                df["mixer"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col2:

        turno = st.selectbox(
            "Turno",
            ["TODOS"]
            + sorted(
                df["turno"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col3:

        estado = st.selectbox(
            "Estado",
            ["TODOS"]
            + sorted(
                df["estado"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col4:

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

    if mixer != "TODOS":

        df_filtrado = df_filtrado[
            df_filtrado["mixer"]
            == mixer
        ]

    if turno != "TODOS":

        df_filtrado = df_filtrado[
            df_filtrado["turno"]
            == turno
        ]

    if estado != "TODOS":

        df_filtrado = df_filtrado[
            df_filtrado["estado"]
            == estado
        ]

    if rango != "Todo":

        fecha_max = (
            df_filtrado["fecha"]
            .max()
        )

        dias = {
            "Últimos 7 días": 7,
            "Últimos 15 días": 15,
            "Últimos 30 días": 30
        }[rango]

        fecha_min = (
            fecha_max
            - pd.Timedelta(
                days=dias - 1
            )
        )

        df_filtrado = df_filtrado[
            df_filtrado["fecha"]
            >= fecha_min
        ]

    if df_filtrado.empty:

        st.warning(
            "No hay registros con los filtros seleccionados."
        )

        return

    df_filtrado = df_filtrado.sort_values(
        "fecha",
        ascending=False
    )

    st.info(
        f"Mixers encontrados: "
        f"**{len(df_filtrado)}**"
    )

    st.markdown("---")

    # ======================================================
    # TARJETAS
    # ======================================================

    for _, row in df_filtrado.iterrows():

        id_despacho = limpiar_texto(
            row.get("id_despacho", "")
        )

        fecha = row[
            "fecha"
        ].strftime("%d/%m/%Y")

        turno = limpiar_texto(
            row.get("turno", "")
        )

        mixer = limpiar_texto(
            row.get("mixer", "")
        )

        codigo_cognos = limpiar_texto(
            row.get(
                "codigo_cognos",
                ""
            )
        )

        supervisor = limpiar_texto(
            row.get(
                "supervisor",
                ""
            )
        )

        llegada = limpiar_texto(
            row.get(
                "hora_llegada",
                ""
            )
        )

        inicio = limpiar_texto(
            row.get(
                "hora_inicio_carga",
                ""
            )
        )

        salida = limpiar_texto(
            row.get(
                "hora_salida",
                ""
            )
        )

        espera = limpiar_texto(
            row.get(
                "tiempo_espera_min",
                "0"
            )
        )

        total = limpiar_texto(
            row.get(
                "tiempo_total_min",
                "0"
            )
        )

        metros = limpiar_texto(
            row.get(
                "metros_cubicos",
                "0"
            )
        )

        causa = limpiar_texto(
            row.get(
                "causa_espera",
                ""
            )
        )

        detalle = limpiar_texto(
            row.get(
                "detalle",
                "Sin observaciones."
            )
        )

        estado = limpiar_texto(
            row.get(
                "estado",
                ""
            )
        )

        foto_base64 = obtener_base64_limpio(
            row.get(
                "evidencia",
                ""
            )
        )

        color = color_estado(
            estado
        )

        if foto_base64:

            bloque_imagen = f"""
            <div class="image-box">
                <img src="data:image/jpeg;base64,{foto_base64}">
                <div class="image-caption">
                    {mixer}
                </div>
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
        <style>

        body {{
            font-family: Arial;
            background: transparent;
        }}

        .container {{
            display:grid;
            grid-template-columns:240px 1fr;
            gap:18px;
            margin-bottom:20px;
        }}

        .image-box {{
            background:#1f1f1f;
            border-radius:14px;
            padding:10px;
            text-align:center;
        }}

        .image-box img {{
            max-width:220px;
            max-height:210px;
            border-radius:10px;
        }}

        .image-caption {{
            color:#cfcfcf;
            margin-top:8px;
            font-size:12px;
        }}

        .no-image {{
            background:#202020;
            border-radius:14px;
            height:250px;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#9e9e9e;
            font-weight:700;
        }}

        .repo-card {{
            background:#1d1d1d;
            border-left:7px solid #00ACC1;
            border-radius:16px;
            padding:18px;
        }}

        .repo-header {{
            display:flex;
            justify-content:space-between;
        }}

        .repo-title {{
            color:white;
            font-size:28px;
            font-weight:900;
        }}

        .repo-subtitle {{
            color:#bdbdbd;
            font-size:13px;
        }}

        .estado {{
            background:{color};
            color:white;
            padding:8px 15px;
            border-radius:18px;
            font-weight:800;
        }}

        .grid {{
            display:grid;
            grid-template-columns:repeat(6,1fr);
            gap:10px;
            margin-top:15px;
        }}

        .box {{
            background:#2c2c2c;
            border-radius:10px;
            padding:10px;
        }}

        .label {{
            color:#9e9e9e;
            font-size:11px;
            text-transform:uppercase;
        }}

        .value {{
            color:white;
            font-weight:800;
        }}

        .section {{
            color:#00ACC1;
            margin-top:12px;
            font-weight:900;
        }}

        .text {{
            color:#efefef;
            line-height:1.4;
        }}

        </style>

        <body>

        <div class="container">

            {bloque_imagen}

            <div class="repo-card">

                <div class="repo-header">

                    <div>
                        <div class="repo-title">
                            {mixer}
                        </div>

                        <div class="repo-subtitle">
                            {id_despacho}
                            · {fecha}
                            · {turno}
                            · {codigo_cognos}
                        </div>
                    </div>

                    <div class="estado">
                        {estado}
                    </div>

                </div>

                <div class="grid">

                    <div class="box">
                        <div class="label">Llegada</div>
                        <div class="value">{llegada}</div>
                    </div>

                    <div class="box">
                        <div class="label">Inicio carga</div>
                        <div class="value">{inicio}</div>
                    </div>

                    <div class="box">
                        <div class="label">Salida</div>
                        <div class="value">{salida}</div>
                    </div>

                    <div class="box">
                        <div class="label">Espera</div>
                        <div class="value">{espera} min</div>
                    </div>

                    <div class="box">
                        <div class="label">Tiempo total</div>
                        <div class="value">{total} min</div>
                    </div>

                    <div class="box">
                        <div class="label">m³</div>
                        <div class="value">{metros}</div>
                    </div>

                </div>

                <div class="section">
                    Causa de espera
                </div>

                <div class="text">
                    {causa}
                </div>

                <div class="section">
                    Observación
                </div>

                <div class="text">
                    {detalle}
                </div>

                <div class="section">
                    Supervisor
                </div>

                <div class="text">
                    {supervisor}
                </div>

            </div>

        </div>

        </body>
        </html>
        """

        components.html(
            html_card,
            height=330,
            scrolling=False
        )