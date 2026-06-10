# ==========================================================
# HISTORIAL_EVENTOS.PY
# BITÁCORA VISUAL DE EVENTOS - SISTEMA DE BOMBEO
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

    st.title("📰 Historial Visual de Eventos")
    st.caption("Bitácora visual para cambio de guardia · Sistema de bombeo")
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

    df["fecha"] = pd.to_datetime(
        df["fecha"],
        errors="coerce"
    )

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

    st.subheader("🔎 Filtros rápidos")

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
            [
                "Últimos 7 días",
                "Últimos 15 días",
                "Últimos 30 días",
                "Todo"
            ]
        )

    df_filtrado = df.copy()

    if nivel != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel]

    if codigo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["codigo"] == codigo]

    if estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado]

    fecha_max = df_filtrado["fecha"].max()

    if rango != "Todo" and pd.notna(fecha_max):

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

    df_filtrado = df_filtrado.sort_values(
        "fecha",
        ascending=False
    )

    st.info(
        f"Eventos encontrados: **{len(df_filtrado)}** · "
        f"Mostrando del más reciente al más antiguo."
    )

    st.markdown("---")

    # ======================================================
    # TARJETAS TIPO PERIÓDICO
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

        with st.container():

            st.markdown(
                f"""
                <div style="
                    border:1px solid rgba(255,255,255,0.15);
                    border-radius:16px;
                    padding:18px;
                    margin-bottom:18px;
                    background:rgba(255,255,255,0.045);
                    box-shadow:0 8px 24px rgba(0,0,0,0.25);
                ">
                    <h3 style="margin-bottom:4px;">
                        🛠️ {evento} · {fecha} · {nivel_txt} · {codigo_txt}
                    </h3>
                    <p style="margin:0;color:#bdbdbd;">
                        Ubicación: <b>{ubicacion}</b> · 
                        Inicio: <b>{hora_falla}</b> · 
                        Fin: <b>{hora_subsanada}</b>
                    </p>
                    <hr style="border:0;border-top:1px solid rgba(255,255,255,0.12);">
                    <p><b>Tipo mantenimiento:</b> {tipo_mantenimiento}</p>
                    <p><b>Tipo de falla / intervención:</b> {tipo_falla}</p>
                    <p><b>Causa preliminar:</b> {causa}</p>
                    <p><b>Detalle / trabajo realizado:</b><br>{descripcion}</p>
                    <p>
                        <b>Estado:</b> {estado_txt} &nbsp;&nbsp; 
                        <b>Registrado por:</b> {tecnico}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            imagen_bytes = obtener_bytes_imagen(foto)

            if imagen_bytes is not None:
                st.image(
                    imagen_bytes,
                    caption=f"Evidencia fotográfica · {evento} · {codigo_txt}",
                    use_container_width=True
                )
            else:
                st.caption("Sin evidencia fotográfica registrada.")

            st.markdown("---")