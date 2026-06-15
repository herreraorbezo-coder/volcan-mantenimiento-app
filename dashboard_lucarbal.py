# ==========================================================
# DASHBOARD_LUCARBAL.PY
# DASHBOARD KPI - LUCARBAL
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

from database import (
    cargar_lucarbal_eventos,
    cargar_equipos_lucarbal,
    refrescar_cache_datos
)


def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


def limpiar_columnas(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df


def normalizar_texto_series(serie):
    return (
        serie.astype(str)
        .str.strip()
        .str.upper()
        .replace({"NAN": "", "NONE": "", "NULL": ""})
    )


def preparar_data():
    df = cargar_lucarbal_eventos()
    equipos = cargar_equipos_lucarbal()

    if df.empty:
        return df, equipos

    df = limpiar_columnas(df)
    equipos = limpiar_columnas(equipos)

    columnas_eventos = [
        "id", "fecha", "turno", "familia_equipo", "codigo_lucarbal",
        "codigo_cognos", "marca", "tipo_mantenimiento", "hora_falla",
        "hora_subsanada", "tiempo_parada", "descripcion", "estado_operativo",
        "tecnico", "dni", "foto", "fecha_registro"
    ]

    columnas_equipos = [
        "familia_equipo", "codigo_lucarbal", "codigo_cognos", "marca"
    ]

    for col in columnas_eventos:
        if col not in df.columns:
            df[col] = ""

    for col in columnas_equipos:
        if col not in equipos.columns:
            equipos[col] = ""

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["tiempo_parada"] = pd.to_numeric(
        df["tiempo_parada"], errors="coerce"
    ).fillna(0).astype(float)

    for col in df.columns:
        if col not in ["fecha", "tiempo_parada"]:
            df[col] = normalizar_texto_series(df[col])

    for col in equipos.columns:
        equipos[col] = normalizar_texto_series(equipos[col])

    df = df.dropna(subset=["fecha"])
    return df, equipos


def calcular_kpis(df, equipos, fecha_ini, fecha_fin, turno):
    dias = (fecha_fin - fecha_ini).days + 1
    if dias <= 0:
        dias = 1

    horas_base_equipo = float(dias * (12 if turno != "TODOS" else 24))
    equipos_base = equipos.copy()
    resumen = []

    for _, eq in equipos_base.iterrows():
        codigo = str(eq.get("codigo_lucarbal", "")).strip().upper()
        cognos = str(eq.get("codigo_cognos", "")).strip().upper()
        familia = str(eq.get("familia_equipo", "")).strip().upper()
        marca = str(eq.get("marca", "")).strip().upper()

        df_eq = df[df["codigo_lucarbal"] == codigo].copy()
        df_eq["tiempo_parada"] = pd.to_numeric(
            df_eq["tiempo_parada"], errors="coerce"
        ).fillna(0).astype(float)

        horas_parada = float(df_eq["tiempo_parada"].sum())
        eventos = int((df_eq["tiempo_parada"] > 0).sum())
        horas_operativas = max(horas_base_equipo - horas_parada, 0)

        disponibilidad = (
            (horas_operativas / horas_base_equipo) * 100
            if horas_base_equipo > 0 else 100
        )
        mttr = horas_parada / eventos if eventos > 0 else 0
        mtbf = horas_operativas / eventos if eventos > 0 else 0

        resumen.append({
            "Familia": familia,
            "Marca": marca,
            "Equipo": codigo,
            "Cognos": cognos,
            "Horas calendario": round(horas_base_equipo, 2),
            "Horas parada": round(horas_parada, 2),
            "Horas operativas": round(horas_operativas, 2),
            "Eventos": eventos,
            "Disponibilidad %": round(disponibilidad, 2),
            "MTTR h": round(mttr, 2),
            "MTBF h": round(mtbf, 2)
        })

    return pd.DataFrame(resumen)


def generar_pdf(df_kpi, df_eventos, fecha_ini, fecha_fin, turno):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=22,
        leftMargin=22,
        topMargin=24,
        bottomMargin=24
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("INFORME KPI LUCARBAL", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Periodo: {fecha_ini} al {fecha_fin}", styles["Normal"]))
    story.append(Paragraph(f"Turno: {turno}", styles["Normal"]))
    story.append(Paragraph(
        f"Fecha generación: {ahora_peru().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 14))

    disp_global = df_kpi["Disponibilidad %"].mean() if not df_kpi.empty else 0
    horas_parada = df_kpi["Horas parada"].sum() if not df_kpi.empty else 0
    eventos = df_kpi["Eventos"].sum() if not df_kpi.empty else 0
    mttr = horas_parada / eventos if eventos > 0 else 0
    horas_operativas = df_kpi["Horas operativas"].sum() if not df_kpi.empty else 0
    mtbf = horas_operativas / eventos if eventos > 0 else 0

    resumen = [
        ["Indicador", "Valor"],
        ["Disponibilidad promedio", f"{disp_global:.2f} %"],
        ["Horas parada", f"{horas_parada:.2f} h"],
        ["Eventos", str(int(eventos))],
        ["MTTR estimado", f"{mttr:.2f} h"],
        ["MTBF estimado", f"{mtbf:.2f} h"]
    ]

    tabla_resumen = Table(resumen, colWidths=[260, 180])
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 8)
    ]))

    story.append(Paragraph("1. Resumen ejecutivo", styles["Heading2"]))
    story.append(tabla_resumen)
    story.append(Spacer(1, 14))

    story.append(Paragraph("2. Disponibilidad por equipo", styles["Heading2"]))
    tabla_kpi = [["Familia", "Equipo", "Cognos", "Disp. %", "H. parada", "Eventos", "MTTR", "MTBF"]]

    for _, r in df_kpi.iterrows():
        tabla_kpi.append([
            str(r["Familia"])[:18],
            str(r["Equipo"])[:14],
            str(r["Cognos"])[:18],
            f'{float(r["Disponibilidad %"]):.2f} %',
            f'{float(r["Horas parada"]):.2f}',
            str(int(r["Eventos"])),
            f'{float(r["MTTR h"]):.2f}',
            f'{float(r["MTBF h"]):.2f}'
        ])

    tabla = Table(tabla_kpi, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))
    story.append(tabla)
    story.append(Spacer(1, 14))

    story.append(Paragraph("3. Detalle de eventos", styles["Heading2"]))
    detalle = [["Fecha", "Turno", "Equipo", "Tipo", "H. parada", "Estado", "Descripcion"]]

    df_eventos = df_eventos.copy()
    if "tiempo_parada" not in df_eventos.columns:
        df_eventos["tiempo_parada"] = 0

    df_eventos["tiempo_parada"] = pd.to_numeric(
        df_eventos["tiempo_parada"], errors="coerce"
    ).fillna(0).astype(float)

    for _, r in df_eventos.iterrows():
        detalle.append([
            r["fecha"].strftime("%d/%m/%Y") if pd.notna(r["fecha"]) else "",
            str(r.get("turno", ""))[:8],
            str(r.get("codigo_lucarbal", ""))[:14],
            str(r.get("tipo_mantenimiento", ""))[:18],
            f'{float(r.get("tiempo_parada", 0)):.2f}',
            str(r.get("estado_operativo", ""))[:14],
            str(r.get("descripcion", ""))[:70]
        ])

    tabla_detalle = Table(detalle, repeatRows=1)
    tabla_detalle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 5.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))
    story.append(tabla_detalle)

    doc.build(story)
    buffer.seek(0)
    return buffer


def mostrar_dashboard_lucarbal():
    st.title("🚛 Dashboard KPI Lucarbal")
    st.caption("Disponibilidad · MTTR · MTBF · Horas de parada · Reporte por turno")

    if st.button("🔄 Actualizar datos", use_container_width=True):
        refrescar_cache_datos()
        st.rerun()

    st.markdown("---")
    df, equipos = preparar_data()

    if df.empty:
        st.warning("No existen eventos registrados en Lucarbal.")
        return

    if equipos.empty:
        st.warning("No existe catálogo de equipos Lucarbal.")
        return

    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fecha_ini = st.date_input("Fecha inicio", value=fecha_min)
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=fecha_max)

    if fecha_fin < fecha_ini:
        st.error("La fecha fin no puede ser menor que la fecha inicio.")
        return

    with col3:
        turno = st.selectbox("Turno", ["TODOS", "DIA", "NOCHE"])
    with col4:
        familia = st.selectbox(
            "Flota",
            ["TODAS"] + sorted(equipos["familia_equipo"].dropna().unique().tolist())
        )

    df_filtrado = df[
        (df["fecha"].dt.date >= fecha_ini) &
        (df["fecha"].dt.date <= fecha_fin)
    ].copy()

    if "turno" not in df_filtrado.columns:
        df_filtrado["turno"] = ""

    if turno != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["turno"] == turno]

    equipos_filtrados = equipos.copy()

    if familia != "TODAS":
        equipos_filtrados = equipos_filtrados[equipos_filtrados["familia_equipo"] == familia]
        df_filtrado = df_filtrado[df_filtrado["familia_equipo"] == familia]

    if equipos_filtrados.empty:
        st.warning("No hay equipos en el catálogo con los filtros seleccionados.")
        return

    if df_filtrado.empty:
        st.warning(
            "No hay eventos con los filtros seleccionados. "
            "Se mostrarán los equipos con disponibilidad 100%."
        )

    df_kpi = calcular_kpis(df_filtrado, equipos_filtrados, fecha_ini, fecha_fin, turno)

    if df_kpi.empty:
        st.warning("No se pudo calcular KPI con la información disponible.")
        return

    disp_global = float(df_kpi["Disponibilidad %"].mean())
    horas_parada = float(df_kpi["Horas parada"].sum())
    eventos = int(df_kpi["Eventos"].sum())
    mttr_global = horas_parada / eventos if eventos > 0 else 0
    horas_operativas = float(df_kpi["Horas operativas"].sum())
    mtbf_global = horas_operativas / eventos if eventos > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Disponibilidad promedio", f"{disp_global:.2f} %")
    c2.metric("Horas parada", f"{horas_parada:.2f} h")
    c3.metric("Eventos", int(eventos))
    c4.metric("MTTR estimado", f"{mttr_global:.2f} h")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("MTBF estimado", f"{mtbf_global:.2f} h")
    c6.metric("Equipos base", len(equipos_filtrados))

    equipo_critico = df_kpi.sort_values("Horas parada", ascending=False).iloc[0]["Equipo"]
    flota_critica = df_kpi.groupby("Familia")["Horas parada"].sum().idxmax()

    c7.metric("Equipo crítico", equipo_critico)
    c8.metric("Flota crítica", flota_critica)

    st.markdown("---")
    st.subheader("📊 Disponibilidad por equipo")

    fig_disp = px.bar(
        df_kpi.sort_values("Disponibilidad %"),
        x="Equipo",
        y="Disponibilidad %",
        color="Familia",
        text="Disponibilidad %",
        hover_data=["Cognos", "Horas parada", "Eventos", "MTTR h", "MTBF h"]
    )
    fig_disp.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_disp.update_layout(yaxis_range=[0, 105])
    st.plotly_chart(fig_disp, use_container_width=True)

    st.subheader("⏱ Horas de parada por equipo")
    fig_parada = px.bar(
        df_kpi.sort_values("Horas parada", ascending=False),
        x="Equipo",
        y="Horas parada",
        color="Familia",
        text="Horas parada",
        hover_data=["Cognos", "Eventos"]
    )
    fig_parada.update_traces(texttemplate="%{text:.1f} h", textposition="outside")
    st.plotly_chart(fig_parada, use_container_width=True)

    st.subheader("🚛 Resumen por flota")
    df_flota = df_kpi.groupby("Familia", as_index=False).agg({
        "Horas calendario": "sum",
        "Horas parada": "sum",
        "Horas operativas": "sum",
        "Eventos": "sum"
    })
    df_flota["Disponibilidad %"] = (
        (df_flota["Horas operativas"] / df_flota["Horas calendario"]) * 100
    ).round(2)
    df_flota["MTTR h"] = (
        df_flota["Horas parada"] / df_flota["Eventos"].replace(0, pd.NA)
    ).fillna(0).round(2)
    df_flota["MTBF h"] = (
        df_flota["Horas operativas"] / df_flota["Eventos"].replace(0, pd.NA)
    ).fillna(0).round(2)
    st.dataframe(df_flota, use_container_width=True)

    st.subheader("🔧 Pareto por tipo de mantenimiento")
    if df_filtrado.empty:
        st.info("No hay eventos para graficar Pareto.")
    else:
        df_filtrado["tiempo_parada"] = pd.to_numeric(
            df_filtrado["tiempo_parada"], errors="coerce"
        ).fillna(0).astype(float)
        df_tipo = df_filtrado.groupby("tipo_mantenimiento", as_index=False).agg({
            "tiempo_parada": "sum",
            "id": "count"
        }).rename(columns={"tiempo_parada": "Horas parada", "id": "Eventos"})
        fig_tipo = px.bar(
            df_tipo.sort_values("Horas parada", ascending=False),
            x="tipo_mantenimiento",
            y="Horas parada",
            text="Horas parada",
            color="tipo_mantenimiento"
        )
        fig_tipo.update_traces(texttemplate="%{text:.1f} h", textposition="outside")
        st.plotly_chart(fig_tipo, use_container_width=True)

    st.subheader("📋 Tabla KPI por equipo")
    st.dataframe(df_kpi, use_container_width=True)

    st.subheader("🧾 Eventos del periodo / turno")
    columnas_eventos = [
        "id", "fecha", "turno", "familia_equipo", "codigo_lucarbal",
        "codigo_cognos", "marca", "tipo_mantenimiento", "hora_falla",
        "hora_subsanada", "tiempo_parada", "estado_operativo", "tecnico", "descripcion"
    ]
    for col in columnas_eventos:
        if col not in df_filtrado.columns:
            df_filtrado[col] = ""

    if df_filtrado.empty:
        st.info("No hay eventos registrados para el filtro seleccionado.")
    else:
        st.dataframe(df_filtrado[columnas_eventos], use_container_width=True)

    st.markdown("---")
    pdf = generar_pdf(df_kpi, df_filtrado, fecha_ini, fecha_fin, turno)
    st.download_button(
        label="📄 Exportar informe PDF",
        data=pdf,
        file_name=f"Informe_Lucarbal_{fecha_ini}_{fecha_fin}_{turno}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
