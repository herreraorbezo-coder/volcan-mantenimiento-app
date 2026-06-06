# ==========================================================
# DASHBOARD_TRACKLESS.PY
# DASHBOARD DE CONFIABILIDAD - FLOTA TRACKLESS
# ==========================================================

import streamlit as st
import pandas as pd
import altair as alt
import base64

from database import cargar_trackless


# ==========================================================
# LISTA MAESTRA DE EQUIPOS TRACKLESS
# ==========================================================

EQUIPOS_TRACKLESS = {
    "JUMBO FRONTONERO": ["JUMBO-007", "JUMBO-008"],
    "EMPERNADOR": ["BOL-212", "BOL-213"],
    "TALADRO LARGO": ["JTL-001", "JTL-002"],
    "SCOOP": ["SCO-313", "SCO-314", "SCO-315", "SCO-316", "SCO-317", "SCO-322"],
    "MIXER": ["MIX-510", "MIX-508", "MIX-509"],
    "LANZADOR": ["ROB-A16", "ROB-A17"],
    "DESATADOR": ["SCA-109", "SCA-110"],
    "UTILITARIO": ["MTM-114", "MTM-115"],
    "PLANTA": ["PLANTA FIJA", "PLANTA MÓVIL"],
    "OTROS": [
        "CISTERNA DE COMBUSTIBLE",
        "INYECTORA DE CEMENTO",
        "CAMION DE MATERIALES"
    ]
}


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


def calcular_disponibilidad(horas_calendario, horas_parada):

    if horas_calendario <= 0:
        return 0

    disponibilidad = (
        (horas_calendario - horas_parada)
        / horas_calendario
    ) * 100

    return max(0, min(disponibilidad, 100))


def mostrar_dashboard_trackless():

    st.title("🚜 Dashboard Trackless - Confiabilidad y Disponibilidad")
    st.caption("Disponibilidad global · Disponibilidad contractual · Paradas atribuibles y no atribuibles")
    st.markdown("---")

    df = cargar_trackless()

    if df.empty:
        st.warning("No existen registros Trackless aún.")
        return

    df.columns = df.columns.str.strip().str.lower()

    columnas_necesarias = [
        "id",
        "fecha",
        "tecnico",
        "turno",
        "familia_equipo",
        "codigo_equipo",
        "hora_parada",
        "hora_reinicio",
        "tiempo_parada",
        "tipo_parada",
        "afecta_global",
        "afecta_contratista",
        "afecta_mtbf",
        "afecta_mttr",
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
        "tecnico",
        "turno",
        "familia_equipo",
        "codigo_equipo",
        "tipo_parada",
        "afecta_global",
        "afecta_contratista",
        "afecta_mtbf",
        "afecta_mttr",
        "estado"
    ]:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.warning("No hay fechas válidas en Trackless.")
        return

    # ======================================================
    # FILTROS
    # ======================================================

    st.subheader("🔎 Filtros")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        familia = st.selectbox(
            "Flota / familia",
            ["TODOS"] + sorted(df["familia_equipo"].dropna().unique().tolist())
        )

    with colf2:
        equipo = st.selectbox(
            "Equipo",
            ["TODOS"] + sorted(df["codigo_equipo"].dropna().unique().tolist())
        )

    with colf3:
        turno = st.selectbox(
            "Turno",
            ["TODOS"] + sorted(df["turno"].dropna().unique().tolist())
        )

    with colf4:
        tipo_parada = st.selectbox(
            "Tipo de parada",
            ["TODOS"] + sorted(df["tipo_parada"].dropna().unique().tolist())
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
            value=fecha_min,
            key="fecha_inicio_trackless_dash"
        )

    with colf7:
        fecha_fin = st.date_input(
            "Fecha fin",
            value=fecha_max,
            key="fecha_fin_trackless_dash"
        )

    df_filtrado = df.copy()

    df_filtrado = df_filtrado[
        (df_filtrado["fecha"].dt.date >= fecha_inicio) &
        (df_filtrado["fecha"].dt.date <= fecha_fin)
    ]

    if familia != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["familia_equipo"] == familia]

    if equipo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["codigo_equipo"] == equipo]

    if turno != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["turno"] == turno]

    if tipo_parada != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["tipo_parada"] == tipo_parada]

    if estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado]

    if df_filtrado.empty:
        st.warning("No hay registros Trackless con los filtros seleccionados.")
        return

    st.markdown("---")

    # ======================================================
    # CHECKBOX DINÁMICO PARA DISPONIBILIDAD AJUSTADA
    # ======================================================

    st.subheader("⚙️ Simulación de disponibilidad ajustada")

    st.caption(
        "Marca o desmarca qué tipos de parada deseas incluir en el cálculo. "
        "Esto permite comparar disponibilidad global vs. disponibilidad atribuible."
    )

    colc1, colc2, colc3, colc4 = st.columns(4)

    with colc1:
        incluir_mantenimiento = st.checkbox(
            "Incluir correctivos / mantenimiento",
            value=True
        )

    with colc2:
        incluir_operacion = st.checkbox(
            "Incluir daño operativo",
            value=True
        )

    with colc3:
        incluir_mina = st.checkbox(
            "Incluir condición mina",
            value=True
        )

    with colc4:
        incluir_seguridad = st.checkbox(
            "Incluir seguridad / implementación",
            value=True
        )

    tipos_incluidos = []

    if incluir_mantenimiento:
        tipos_incluidos += [
            "PARADA CORRECTIVO NO PROGRAMADO",
            "PARADA CORRECTIVO PROGRAMADO",
            "PARADA MANTENIMIENTO PREVENTIVO"
        ]

    if incluir_operacion:
        tipos_incluidos += [
            "PARADA DAÑO OPERATIVO"
        ]

    if incluir_mina:
        tipos_incluidos += [
            "PARADA CONDICIÓN DE MINA"
        ]

    if incluir_seguridad:
        tipos_incluidos += [
            "PARADA DE SEGURIDAD",
            "PARADA POR IMPLEMENTACIÓN EQUIPO"
        ]

    df_ajustado = df_filtrado[
        df_filtrado["tipo_parada"].isin(tipos_incluidos)
    ].copy()

    # ======================================================
    # BASE 24 HORAS
    # ======================================================

    dias_periodo = (
        fecha_fin - fecha_inicio
    ).days + 1

    if equipo != "TODOS":
        cantidad_equipos_base = 1

    elif familia != "TODOS":
        cantidad_equipos_base = len(
            EQUIPOS_TRACKLESS.get(familia, df_filtrado["codigo_equipo"].unique())
        )

    else:
        cantidad_equipos_base = len(
            [eq for lista in EQUIPOS_TRACKLESS.values() for eq in lista]
        )

    horas_calendario = dias_periodo * 24 * max(cantidad_equipos_base, 1)

    # ======================================================
    # KPIs
    # ======================================================

    total_eventos = len(df_filtrado)

    horas_globales = df_filtrado[
        df_filtrado["afecta_global"].str.upper() == "SI"
    ]["tiempo_parada"].sum()

    horas_contratista = df_filtrado[
        df_filtrado["afecta_contratista"].str.upper() == "SI"
    ]["tiempo_parada"].sum()

    horas_ajustadas = df_ajustado["tiempo_parada"].sum()

    disponibilidad_global = calcular_disponibilidad(
        horas_calendario,
        horas_globales
    )

    disponibilidad_contractual = calcular_disponibilidad(
        horas_calendario,
        horas_contratista
    )

    disponibilidad_ajustada = calcular_disponibilidad(
        horas_calendario,
        horas_ajustadas
    )

    eventos_mtbf = df_filtrado[
        df_filtrado["afecta_mtbf"].str.upper() == "SI"
    ].shape[0]

    horas_mttr = df_filtrado[
        df_filtrado["afecta_mttr"].str.upper() == "SI"
    ]["tiempo_parada"].sum()

    eventos_mttr = df_filtrado[
        df_filtrado["afecta_mttr"].str.upper() == "SI"
    ].shape[0]

    mtbf = (
        (horas_calendario - horas_contratista) / eventos_mtbf
        if eventos_mtbf > 0
        else 0
    )

    mttr = (
        horas_mttr / eventos_mttr
        if eventos_mttr > 0
        else 0
    )

    equipo_critico = (
        df_filtrado.groupby("codigo_equipo")["tiempo_parada"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
        if not df_filtrado.empty
        else "-"
    )

    flota_critica = (
        df_filtrado.groupby("familia_equipo")["tiempo_parada"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
        if not df_filtrado.empty
        else "-"
    )

    st.markdown("---")

    st.subheader("📌 KPIs Trackless")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Disponibilidad Global", f"{round(disponibilidad_global, 2)} %")
    k2.metric("Disponibilidad Contractual", f"{round(disponibilidad_contractual, 2)} %")
    k3.metric("Disponibilidad Ajustada", f"{round(disponibilidad_ajustada, 2)} %")
    k4.metric("Horas calendario", round(horas_calendario, 2))

    k5, k6, k7, k8 = st.columns(4)

    k5.metric("Horas parada global", round(horas_globales, 2))
    k6.metric("Horas atribuibles contratista", round(horas_contratista, 2))
    k7.metric("MTBF contractual", f"{round(mtbf, 2)} h")
    k8.metric("MTTR mantenimiento", f"{round(mttr, 2)} h")

    k9, k10, k11, k12 = st.columns(4)

    k9.metric("Eventos registrados", total_eventos)
    k10.metric("Equipo crítico", equipo_critico)
    k11.metric("Flota crítica", flota_critica)
    k12.metric("Equipos base", cantidad_equipos_base)

    st.info(
        f"Periodo analizado: **{dias_periodo} días** · "
        f"Base de cálculo: **24 h/día por equipo**"
    )

    st.markdown("---")

    # ======================================================
    # TABLA RESUMEN ATRIBUIBLE VS NO ATRIBUIBLE
    # ======================================================

    st.subheader("🧾 Resumen por tipo de parada")

    df_resumen_tipo = (
        df_filtrado
        .groupby("tipo_parada")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
    )

    st.dataframe(
        df_resumen_tipo,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ======================================================
    # GRÁFICOS
    # ======================================================

    st.subheader("📈 Análisis gráfico Trackless")

    # 1. Pareto de indisponibilidad por tipo de parada

    st.markdown("### 1. Pareto de indisponibilidad por tipo de parada")

    chart_tipo_parada = (
        alt.Chart(df_resumen_tipo)
        .mark_bar()
        .encode(
            x=alt.X("tiempo_parada:Q", title="Horas de parada"),
            y=alt.Y("tipo_parada:N", sort="-x", title="Tipo de parada"),
            tooltip=[
                "tipo_parada",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_tipo_parada, use_container_width=True)

    # 2. Horas atribuibles vs no atribuibles

    st.markdown("### 2. Horas atribuibles vs no atribuibles")

    horas_no_atribuibles = max(
        horas_globales - horas_contratista,
        0
    )

    df_atribucion = pd.DataFrame({
        "clasificacion": [
            "Atribuible contratista",
            "No atribuible contratista"
        ],
        "horas": [
            horas_contratista,
            horas_no_atribuibles
        ]
    })

    chart_atribucion = (
        alt.Chart(df_atribucion)
        .mark_bar()
        .encode(
            x=alt.X("clasificacion:N", title="Clasificación"),
            y=alt.Y("horas:Q", title="Horas"),
            tooltip=[
                "clasificacion",
                alt.Tooltip("horas:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_atribucion, use_container_width=True)

    # 3. Top equipos críticos

    st.markdown("### 3. Top equipos críticos por horas de parada")

    df_top_equipos = (
        df_filtrado
        .groupby("codigo_equipo")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
        .head(15)
    )

    chart_top_equipos = (
        alt.Chart(df_top_equipos)
        .mark_bar()
        .encode(
            x=alt.X("tiempo_parada:Q", title="Horas de parada"),
            y=alt.Y("codigo_equipo:N", sort="-x", title="Equipo"),
            tooltip=[
                "codigo_equipo",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_top_equipos, use_container_width=True)

    # 4. Horas de parada por flota

    st.markdown("### 4. Horas de parada por flota")

    df_flota = (
        df_filtrado
        .groupby("familia_equipo")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
    )

    chart_flota = (
        alt.Chart(df_flota)
        .mark_bar()
        .encode(
            x=alt.X("tiempo_parada:Q", title="Horas de parada"),
            y=alt.Y("familia_equipo:N", sort="-x", title="Flota"),
            tooltip=[
                "familia_equipo",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_flota, use_container_width=True)

    # 5. Disponibilidad por equipo

    st.markdown("### 5. Disponibilidad global por equipo")

    df_equipo_horas = (
        df_filtrado
        .groupby("codigo_equipo")["tiempo_parada"]
        .sum()
        .reset_index()
    )

    df_equipo_horas["horas_calendario"] = dias_periodo * 24

    df_equipo_horas["disponibilidad_global"] = (
        (
            df_equipo_horas["horas_calendario"]
            - df_equipo_horas["tiempo_parada"]
        )
        / df_equipo_horas["horas_calendario"]
    ) * 100

    df_equipo_horas["disponibilidad_global"] = (
        df_equipo_horas["disponibilidad_global"]
        .clip(lower=0, upper=100)
    )

    chart_disp_equipo = (
        alt.Chart(df_equipo_horas)
        .mark_bar()
        .encode(
            x=alt.X("disponibilidad_global:Q", title="Disponibilidad global (%)"),
            y=alt.Y("codigo_equipo:N", sort="-x", title="Equipo"),
            tooltip=[
                "codigo_equipo",
                alt.Tooltip("disponibilidad_global:Q", format=".2f"),
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_disp_equipo, use_container_width=True)

    # 6. Disponibilidad por flota

    st.markdown("### 6. Disponibilidad global por flota")

    df_flota_disp = (
        df_filtrado
        .groupby("familia_equipo")["tiempo_parada"]
        .sum()
        .reset_index()
    )

    df_flota_disp["cantidad_equipos"] = df_flota_disp["familia_equipo"].apply(
        lambda x: len(EQUIPOS_TRACKLESS.get(x, []))
    )

    df_flota_disp["horas_calendario"] = (
        dias_periodo
        * 24
        * df_flota_disp["cantidad_equipos"]
    )

    df_flota_disp["disponibilidad_global"] = (
        (
            df_flota_disp["horas_calendario"]
            - df_flota_disp["tiempo_parada"]
        )
        / df_flota_disp["horas_calendario"]
    ) * 100

    df_flota_disp["disponibilidad_global"] = (
        df_flota_disp["disponibilidad_global"]
        .clip(lower=0, upper=100)
    )

    chart_disp_flota = (
        alt.Chart(df_flota_disp)
        .mark_bar()
        .encode(
            x=alt.X("disponibilidad_global:Q", title="Disponibilidad global (%)"),
            y=alt.Y("familia_equipo:N", sort="-x", title="Flota"),
            tooltip=[
                "familia_equipo",
                alt.Tooltip("disponibilidad_global:Q", format=".2f"),
                alt.Tooltip("tiempo_parada:Q", format=".2f"),
                "cantidad_equipos"
            ]
        )
    )

    st.altair_chart(chart_disp_flota, use_container_width=True)

    # 7. Tendencia diaria

    st.markdown("### 7. Tendencia diaria de horas de parada")

    df_tendencia = (
        df_filtrado
        .groupby(df_filtrado["fecha"].dt.date)["tiempo_parada"]
        .sum()
        .reset_index()
    )

    chart_tendencia = (
        alt.Chart(df_tendencia)
        .mark_line(point=True)
        .encode(
            x=alt.X("fecha:T", title="Fecha"),
            y=alt.Y("tiempo_parada:Q", title="Horas de parada"),
            tooltip=[
                "fecha:T",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_tendencia, use_container_width=True)

    st.markdown("---")

    # ======================================================
    # HISTORIAL
    # ======================================================

    st.subheader("📋 Historial Trackless")

    columnas_mostrar = [
        "id",
        "fecha",
        "turno",
        "tecnico",
        "familia_equipo",
        "codigo_equipo",
        "hora_parada",
        "hora_reinicio",
        "tiempo_parada",
        "tipo_parada",
        "afecta_global",
        "afecta_contratista",
        "afecta_mtbf",
        "afecta_mttr",
        "descripcion",
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

    st.subheader("📷 Evidencia fotográfica Trackless")

    eventos_con_foto = df_filtrado[
        df_filtrado["foto"].astype(str).str.contains("base64", na=False)
    ].copy()

    if eventos_con_foto.empty:
        st.info("No hay evidencias fotográficas en los registros filtrados.")
    else:
        eventos_con_foto["selector"] = (
            eventos_con_foto["id"].astype(str) + " | " +
            eventos_con_foto["codigo_equipo"].astype(str) + " | " +
            eventos_con_foto["tipo_parada"].astype(str) + " | " +
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
                caption=f"Evidencia {fila['id']} - {fila['codigo_equipo']}",
                use_container_width=True
            )

            st.download_button(
                label="⬇️ Descargar evidencia JPG",
                data=imagen_bytes,
                file_name=f"evidencia_{fila['id']}_{fila['codigo_equipo']}.jpg",
                mime="image/jpeg"
            )

    st.markdown("---")

    # ======================================================
    # DESCARGA CSV
    # ======================================================

    csv = df_tabla.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Descargar historial Trackless CSV",
        data=csv,
        file_name="historial_trackless.csv",
        mime="text/csv"
    )