# ==========================================================
# HISTORIAL_EVENTOS.PY
# BITÁCORA VISUAL / PERIÓDICO DE MANTENIMIENTO
# ==========================================================

import streamlit as st
import pandas as pd
import base64

from database import cargar_bitacora


def obtener_bytes_imagen(foto_base64):

    if not isinstance(foto_base64, str):
        return None

    if foto_base64.strip() in ["", "SIN FOTO", "nan", "None"]:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split("base64,")[1]

    try:
        return base64.b64decode(foto_base64)
    except Exception:
        return None


def mostrar_historial_eventos():

    st.title("📰 Bitácora Visual de Mantenimiento")
    st.caption("Eventos recientes del sistema de bombeo · Cambio de guardia")
    st.markdown("---")

    df = cargar_bitacora()

    if df.empty:
        st.warning("No existen eventos registrados.")
        return

    df.columns = df.columns.str.strip().str.lower()

    columnas_necesarias = [
        "id", "fecha", "nivel", "ubicacion", "codigo",
        "hora_falla", "hora_subsanada", "tipo_mantenimiento",
        "tipo_falla", "causa_preliminar", "descripcion",
        "estado", "tecnico", "foto"
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

        df_filtrado = df_filtrado[df_filtrado["fecha"] >= fecha_min]

    if df_filtrado.empty:
        st.warning("No hay eventos con los filtros seleccionados.")
        return

    df_filtrado = df_filtrado.sort_values("fecha", ascending=False)

    st.info(f"Eventos encontrados: **{len(df_filtrado)}**")
    st.markdown("---")

    # ======================================================
    # ESTILO TIPO BOLETÍN
    # ======================================================

    st.markdown(
        """
        <style>
        .boletin-card {
            background: #ffffff;
            color: #111111;
            border-radius: 6px;
            margin-bottom: 34px;
            padding: 0px 0px 20px 0px;
            border: 1px solid #d0d0d0;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.25);
        }

        .boletin-title {
            background: #b71c1c;
            color: white;
            padding: 12px 18px;
            font-size: 22px;
            font-weight: 900;
            letter-spacing: .5px;
            border-radius: 6px 6px 0px 0px;
        }

        .boletin-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin-bottom: 12px;
        }

        .boletin-table th {
            background: #b71c1c;
            color: white;
            padding: 10px;
            text-align: center;
            border: 1px solid #8e1111;
            font-weight: 800;
        }

        .boletin-table td {
            padding: 10px;
            text-align: center;
            border: 1px solid #9e9e9e;
            vertical-align: middle;
        }

        .detalle-box {
            padding: 14px 22px;
            font-size: 15px;
            line-height: 1.45;
        }

        .detalle-titulo {
            font-weight: 900;
            color: #b71c1c;
            margin-bottom: 6px;
        }

        .tag-sub {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 14px;
            background: #e8f5e9;
            color: #1b5e20;
            font-size: 12px;
            font-weight: 800;
            margin-right: 6px;
        }

        .tag-info {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 14px;
            background: #e3f2fd;
            color: #0d47a1;
            font-size: 12px;
            font-weight: 800;
            margin-right: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ======================================================
    # TARJETAS
    # ======================================================

    for _, row in df_filtrado.iterrows():

        evento = row.get("id", "")
        fecha = row["fecha"].strftime("%d/%m/%Y")
        nivel_txt = row.get("nivel", "")
        ubicacion = row.get("ubicacion", "")
        codigo_txt = row.get("codigo", "")
        hora_falla = row.get("hora_falla", "")
        hora_subsanada = row.get("hora_subsanada", "")
        tipo_mantenimiento = row.get("tipo_mantenimiento", "")
        tipo_falla = row.get("tipo_falla", "")
        causa = row.get("causa_preliminar", "")
        descripcion = row.get("descripcion", "")
        estado_txt = row.get("estado", "")
        tecnico = row.get("tecnico", "")
        foto = row.get("foto", "")

        st.markdown(
            f"""
            <div class="boletin-card">
                <div class="boletin-title">
                    🛠️ EVENTO DE MANTENIMIENTO - {evento}
                </div>

                <table class="boletin-table">
                    <tr>
                        <th>EVENTO</th>
                        <th>FECHA</th>
                        <th>NIVEL</th>
                        <th>UBICACIÓN</th>
                        <th>CÓDIGO</th>
                        <th>ESTADO</th>
                    </tr>
                    <tr>
                        <td>{evento}</td>
                        <td>{fecha}</td>
                        <td>{nivel_txt}</td>
                        <td>{ubicacion}</td>
                        <td><b>{codigo_txt}</b></td>
                        <td><b>{estado_txt}</b></td>
                    </tr>
                </table>

                <div class="detalle-box">
                    <span class="tag-sub">Inicio: {hora_falla}</span>
                    <span class="tag-sub">Fin: {hora_subsanada}</span>
                    <span class="tag-info">{tipo_mantenimiento}</span>

                    <br><br>

                    <div class="detalle-titulo">DETALLE / TRABAJO REALIZADO</div>
                    {descripcion}

                    <br><br>

                    <div class="detalle-titulo">TIPO DE FALLA / INTERVENCIÓN</div>
                    {tipo_falla}

                    <br><br>

                    <div class="detalle-titulo">CAUSA PRELIMINAR</div>
                    {causa}

                    <br><br>

                    <b>Registrado por:</b> {tecnico}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        imagen_bytes = obtener_bytes_imagen(foto)

        if imagen_bytes is not None:
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                st.image(
                    imagen_bytes,
                    caption=f"Evidencia fotográfica · {evento} · {codigo_txt}",
                    use_container_width=True
                )
        else:
            st.caption("Sin evidencia fotográfica registrada.")

        st.markdown("<br>", unsafe_allow_html=True)
