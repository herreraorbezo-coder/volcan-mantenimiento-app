# ==========================================================
# DASHBOARD.PY
# DASHBOARD / HISTORIAL DE EVENTOS - VOLCAN APP
# ==========================================================

import streamlit as st
import pandas as pd
import altair as alt
import base64

from database import cargar_bitacora


def obtener_bytes_imagen(foto_base64):

    if not isinstance(foto_base64, str):
        return None

    if foto_base64.strip() in ["", "SIN FOTO"]:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split("base64,")[1]

    try:
        return base64.b64decode(foto_base64)

    except Exception:
        return None


def mostrar_dashboard():

    st.title("📊 Dashboard de Eventos - Sistema Bombeo")
    st.caption("Mantenimiento Mecánico · Planeamiento · Confiabilidad")
    st.markdown("---")

    df = cargar_bitacora()

    if df.empty:
        st.warning("No existen registros aún.")
        return

    df.columns = df.columns.str.strip().str.lower()

    columnas_necesarias = [
        "id",
        "fecha",
        "tecnico",
        "sistema",
        "nivel",
        "ubicacion",
        "codigo",
        "hora_falla",
        "hora_subsanada",
        "tiempo_parada",
        "tipo_falla",
        "causa_preliminar",
        "repuesto_requerido",
        "descripcion",
        "estado",
        "foto"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    df["fecha"] = pd.to_datetime(
        df["fecha"],
        errors="coerce"
    )

    df["tiempo_parada"] = pd.to_numeric(
        df["tiempo_parada"],
        errors="coerce"
    ).fillna(0)

    for col in [
        "codigo",
        "nivel",
        "tipo_falla",
        "causa_preliminar",
        "repuesto_requerido",
        "estado",
        "tecnico"
    ]:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.warning("No hay fechas válidas en la bitácora.")
        return

    # ======================================================
    # FILTROS
    # ======================================================

    st.subheader("🔎 Filtros")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        nivel = st.selectbox(
            "Nivel",
            ["TODOS"] + sorted(df["nivel"].dropna().unique().tolist())
        )

    with colf2:
        bomba = st.selectbox(
            "Bomba",
            ["TODOS"] + sorted(df["codigo"].dropna().unique().tolist())
        )

    with colf3:
        falla = st.selectbox(
            "Tipo de falla",
            ["TODOS"] + sorted(df["tipo_falla"].dropna().unique().tolist())
        )

    with colf4:
        causa = st.selectbox(
            "Causa preliminar",
            ["TODOS"] + sorted(df["causa_preliminar"].dropna().unique().tolist())
        )

    colf5, colf6, colf7 = st.columns(3)

    with colf5:
        estado = st.selectbox(
            "Estado",
            ["TODOS"] + sorted(df["estado"].dropna().unique().tolist())
        )

    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    with colf6:
        fecha_inicio = st.date_input(
            "Fecha inicio",
            value=fecha_min
        )

    with colf7:
        fecha_fin = st.date_input(
            "Fecha fin",
            value=fecha_max
        )

    df_filtrado = df.copy()

    df_filtrado = df_filtrado[
        (df_filtrado["fecha"].dt.date >= fecha_inicio) &
        (df_filtrado["fecha"].dt.date <= fecha_fin)
    ]

    if nivel != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel]

    if bomba != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["codigo"] == bomba]

    if falla != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["tipo_falla"] == falla]

    if causa != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["causa_preliminar"] == causa]

    if estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado]

    if df_filtrado.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

    st.markdown("---")

    # ======================================================
    # KPIs EJECUTIVOS
    # ======================================================

    total_eventos = len(df_filtrado)
    total_horas = df_filtrado["tiempo_parada"].sum()
    mttr = df_filtrado["tiempo_parada"].mean()

    dias_periodo = (
        fecha_fin - fecha_inicio
    ).days + 1

    bombas_involucradas = df_filtrado["codigo"].nunique()

    horas_calendario = dias_periodo * 24 * max(bombas_involucradas, 1)

    disponibilidad = (
        ((horas_calendario - total_horas) / horas_calendario) * 100
        if horas_calendario > 0
        else 0
    )

    disponibilidad = max(0, min(disponibilidad, 100))

    if total_eventos > 1:
        mtbf = round(
            (horas_calendario - total_horas) / total_eventos,
            2
        )
    else:
        mtbf = 0

    bomba_top = (
        df_filtrado.groupby("codigo")["tiempo_parada"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
        if not df_filtrado.empty
        else "-"
    )

    falla_top = (
        df_filtrado["tipo_falla"].mode()[0]
        if not df_filtrado["tipo_falla"].empty
        else "-"
    )

    causa_top = (
        df_filtrado["causa_preliminar"].mode()[0]
        if not df_filtrado["causa_preliminar"].empty
        else "-"
    )

    eventos_pendientes = df_filtrado[
        df_filtrado["estado"].str.upper().isin(
            ["PENDIENTE", "FUERA DE SERVICIO", "EN SEGUIMIENTO"]
        )
    ].shape[0]

    repuestos_requeridos = df_filtrado[
        df_filtrado["repuesto_requerido"].astype(str).str.strip() != ""
    ].shape[0]

    tecnicos_involucrados = df_filtrado["tecnico"].nunique()

    st.subheader("📌 Indicadores ejecutivos")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Eventos", total_eventos)
    k2.metric("Horas parada", round(total_horas, 2))
    k3.metric("Disponibilidad mecánica", f"{round(disponibilidad, 2)} %")
    k4.metric("MTTR promedio", f"{round(mttr, 2)} h")

    k5, k6, k7, k8 = st.columns(4)

    k5.metric("MTBF estimado", f"{mtbf} h")
    k6.metric("Bomba crítica", bomba_top)
    k7.metric("Eventos pendientes", eventos_pendientes)
    k8.metric("Repuestos requeridos", repuestos_requeridos)

    cinfo1, cinfo2, cinfo3 = st.columns(3)

    cinfo1.info(f"Falla más común: **{falla_top}**")
    cinfo2.info(f"Causa más común: **{causa_top}**")
    cinfo3.info(f"Técnicos involucrados: **{tecnicos_involucrados}**")

    st.markdown("---")

    # ======================================================
    # TABLA DE REQUERIMIENTOS DE REPUESTOS
    # ======================================================

    st.subheader("🧩 Repuestos requeridos / pendientes")

    df_repuestos = df_filtrado[
        df_filtrado["repuesto_requerido"].astype(str).str.strip() != ""
    ].copy()

    if df_repuestos.empty:
        st.info("No hay repuestos requeridos en los registros filtrados.")
    else:
        columnas_repuestos = [
            "fecha",
            "codigo",
            "nivel",
            "ubicacion",
            "repuesto_requerido",
            "estado",
            "tecnico"
        ]

        df_repuestos_tabla = df_repuestos[columnas_repuestos].copy()
        df_repuestos_tabla["fecha"] = df_repuestos_tabla["fecha"].dt.strftime("%d/%m/%Y")

        st.dataframe(
            df_repuestos_tabla,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # ======================================================
    # ANÁLISIS GRÁFICO V2
    # ======================================================

    st.subheader("📈 Análisis gráfico gerencial")

    # ======================================================
    # 1. ESTADO DE EVENTOS
    # ======================================================

    st.markdown("### 1. Estado de eventos")

    df_estado = (
        df_filtrado
        .groupby("estado")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    if not df_estado.empty:

        chart_estado = (
            alt.Chart(df_estado)
            .mark_arc(innerRadius=60)
            .encode(
                theta=alt.Theta("cantidad:Q"),
                color=alt.Color("estado:N", title="Estado"),
                tooltip=["estado", "cantidad"]
            )
        )

        st.altair_chart(chart_estado, use_container_width=True)

    # ======================================================
    # 2. TOP BOMBAS CRÍTICAS
    # ======================================================

    st.markdown("### 2. Top 10 bombas críticas por horas de parada")

    df_top_bombas = (
        df_filtrado
        .groupby("codigo")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
        .head(10)
    )

    chart_top_bombas = (
        alt.Chart(df_top_bombas)
        .mark_bar()
        .encode(
            x=alt.X("tiempo_parada:Q", title="Horas de parada"),
            y=alt.Y("codigo:N", sort="-x", title="Bomba"),
            tooltip=[
                "codigo",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_top_bombas, use_container_width=True)

    # ======================================================
    # 3. PARETO DE FALLAS
    # ======================================================

    st.markdown("### 3. Pareto de fallas")

    df_pareto_falla = (
        df_filtrado
        .groupby("tipo_falla")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    chart_pareto_falla = (
        alt.Chart(df_pareto_falla)
        .mark_bar()
        .encode(
            x=alt.X("tipo_falla:N", sort="-y", title="Tipo de falla"),
            y=alt.Y("cantidad:Q", title="Cantidad"),
            tooltip=["tipo_falla", "cantidad"]
        )
    )

    st.altair_chart(chart_pareto_falla, use_container_width=True)

    # ======================================================
    # 4. PARETO DE CAUSAS
    # ======================================================

    st.markdown("### 4. Pareto de causas preliminares")

    df_pareto_causa = (
        df_filtrado
        .groupby("causa_preliminar")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    chart_pareto_causa = (
        alt.Chart(df_pareto_causa)
        .mark_bar()
        .encode(
            x=alt.X("causa_preliminar:N", sort="-y", title="Causa preliminar"),
            y=alt.Y("cantidad:Q", title="Cantidad"),
            tooltip=["causa_preliminar", "cantidad"]
        )
    )

    st.altair_chart(chart_pareto_causa, use_container_width=True)

    # ======================================================
    # 5. REPUESTOS MÁS SOLICITADOS
    # ======================================================

    st.markdown("### 5. Repuestos más solicitados")

    df_rep_chart = df_filtrado[
        df_filtrado["repuesto_requerido"].astype(str).str.strip() != ""
    ].copy()

    if df_rep_chart.empty:
        st.info("No hay repuestos registrados para graficar.")
    else:
        df_rep_chart = (
            df_rep_chart
            .groupby("repuesto_requerido")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        chart_repuestos = (
            alt.Chart(df_rep_chart)
            .mark_bar()
            .encode(
                x=alt.X("cantidad:Q", title="Cantidad"),
                y=alt.Y("repuesto_requerido:N", sort="-x", title="Repuesto"),
                tooltip=["repuesto_requerido", "cantidad"]
            )
        )

        st.altair_chart(chart_repuestos, use_container_width=True)

    # ======================================================
    # 6. HORAS DE PARADA POR NIVEL
    # ======================================================

    st.markdown("### 6. Horas de parada por nivel")

    df_horas_nivel = (
        df_filtrado
        .groupby("nivel")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
    )

    chart_horas_nivel = (
        alt.Chart(df_horas_nivel)
        .mark_bar()
        .encode(
            x=alt.X("nivel:N", sort="-y", title="Nivel"),
            y=alt.Y("tiempo_parada:Q", title="Horas de parada"),
            tooltip=[
                "nivel",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_horas_nivel, use_container_width=True)

    # ======================================================
    # 7. EVENTOS POR TÉCNICO
    # ======================================================

    st.markdown("### 7. Eventos por técnico")

    df_tecnico = (
        df_filtrado
        .groupby("tecnico")
        .size()
        .reset_index(name="eventos")
        .sort_values("eventos", ascending=False)
    )

    chart_tecnico = (
        alt.Chart(df_tecnico)
        .mark_bar()
        .encode(
            x=alt.X("eventos:Q", title="Eventos"),
            y=alt.Y("tecnico:N", sort="-x", title="Técnico"),
            tooltip=["tecnico", "eventos"]
        )
    )

    st.altair_chart(chart_tecnico, use_container_width=True)

    # ======================================================
    # 8. TENDENCIA DIARIA
    # ======================================================

    st.markdown("### 8. Tendencia diaria de eventos")

    df_tendencia = (
        df_filtrado
        .groupby(df_filtrado["fecha"].dt.date)
        .size()
        .reset_index(name="eventos")
    )

    chart_tendencia = (
        alt.Chart(df_tendencia)
        .mark_line(point=True)
        .encode(
            x=alt.X("fecha:T", title="Fecha"),
            y=alt.Y("eventos:Q", title="Eventos"),
            tooltip=["fecha:T", "eventos"]
        )
    )

    st.altair_chart(chart_tendencia, use_container_width=True)

    st.markdown("---")

    # ======================================================
    # HISTORIAL
    # ======================================================

    st.subheader("📋 Historial de Eventos")

    columnas_mostrar = [
        "id",
        "fecha",
        "tecnico",
        "nivel",
        "ubicacion",
        "codigo",
        "tipo_falla",
        "causa_preliminar",
        "repuesto_requerido",
        "descripcion",
        "hora_falla",
        "hora_subsanada",
        "tiempo_parada",
        "estado",
        "foto"
    ]

    df_tabla = df_filtrado[columnas_mostrar].copy()

    df_tabla["fecha"] = df_tabla["fecha"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ======================================================
    # EVIDENCIA FOTOGRÁFICA
    # ======================================================

    st.subheader("📷 Evidencia fotográfica")

    eventos_con_foto = df_filtrado[
        df_filtrado["foto"].astype(str).str.contains("base64", na=False)
    ].copy()

    if eventos_con_foto.empty:
        st.info("No hay evidencias fotográficas en los registros filtrados.")
    else:
        eventos_con_foto["selector"] = (
            eventos_con_foto["id"].astype(str) + " | " +
            eventos_con_foto["codigo"].astype(str) + " | " +
            eventos_con_foto["tipo_falla"].astype(str) + " | " +
            eventos_con_foto["fecha"].dt.strftime("%d/%m/%Y")
        )

        seleccion = st.selectbox(
            "Selecciona evento para ver evidencia",
            eventos_con_foto["selector"].tolist()
        )

        fila = eventos_con_foto[
            eventos_con_foto["selector"] == seleccion
        ].iloc[0]

        imagen_bytes = obtener_bytes_imagen(fila["foto"])

        if imagen_bytes is None:
            st.warning("No se pudo leer la imagen.")
        else:
            st.image(
                imagen_bytes,
                caption=f"Evidencia {fila['id']} - {fila['codigo']}",
                use_container_width=True
            )

            st.download_button(
                label="⬇️ Descargar evidencia JPG",
                data=imagen_bytes,
                file_name=f"evidencia_{fila['id']}_{fila['codigo']}.jpg",
                mime="image/jpeg"
            )

    st.markdown("---")

    # ======================================================
    # DESCARGA CSV
    # ======================================================

    csv = df_tabla.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Descargar historial CSV",
        data=csv,
        file_name="historial_eventos_bombeo.csv",
        mime="text/csv"
    )