# ==========================================================
# DASHBOARD_LUCARBAL.PY
# DASHBOARD KPI - LUCARBAL
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import base64

from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database import (
    cargar_lucarbal_eventos,
    cargar_lucarbal_taller,
    cargar_equipos_lucarbal,
    refrescar_cache_datos
)


# ==========================================================
# UTILIDADES
# ==========================================================

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


def convertir_numero(df, columna):
    if columna not in df.columns:
        df[columna] = 0

    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    ).fillna(0).astype(float)

    return df


def convertir_fecha(df, columna="fecha"):
    if columna not in df.columns:
        df[columna] = ""

    df[columna] = pd.to_datetime(
        df[columna],
        errors="coerce"
    )

    return df


def extraer_imagen_base64(valor):
    try:
        if not isinstance(valor, str):
            return None

        valor = valor.strip()

        if valor == "":
            return None

        if valor.upper() == "SIN FOTO":
            return None

        if "," in valor:
            valor = valor.split(",", 1)[1]

        imagen_bytes = base64.b64decode(valor)

        return BytesIO(imagen_bytes)

    except Exception:
        return None


# ==========================================================
# PREPARAR DATA EVENTOS
# ==========================================================

def preparar_eventos():

    df = cargar_lucarbal_eventos()
    equipos = cargar_equipos_lucarbal()

    if df.empty:
        return df, equipos

    df = limpiar_columnas(df)
    equipos = limpiar_columnas(equipos)

    columnas_eventos = [
        "id",
        "fecha",
        "turno",
        "familia_equipo",
        "codigo_lucarbal",
        "codigo_cognos",
        "marca",
        "tipo_mantenimiento",
        "hora_falla",
        "hora_subsanada",
        "tiempo_parada",
        "descripcion",
        "estado_operativo",
        "tecnico",
        "dni",
        "foto",
        "fecha_registro",
        "hora_inicio_atencion",
        "tiempo_respuesta",
        "tiempo_reparacion",
        "requiere_repuesto",
        "detalle_repuesto",
        "apoyo_1",
        "apoyo_2"
    ]

    columnas_equipos = [
        "familia_equipo",
        "codigo_lucarbal",
        "codigo_cognos",
        "marca"
    ]

    for col in columnas_eventos:
        if col not in df.columns:
            df[col] = ""

    for col in columnas_equipos:
        if col not in equipos.columns:
            equipos[col] = ""

    df = convertir_fecha(df, "fecha")
    df = convertir_numero(df, "tiempo_parada")
    df = convertir_numero(df, "tiempo_respuesta")
    df = convertir_numero(df, "tiempo_reparacion")

    # No normalizar foto porque malogra el base64
    columnas_no_normalizar = [
        "fecha",
        "tiempo_parada",
        "tiempo_respuesta",
        "tiempo_reparacion",
        "foto"
    ]

    for col in df.columns:
        if col not in columnas_no_normalizar:
            df[col] = normalizar_texto_series(df[col])

    for col in equipos.columns:
        equipos[col] = normalizar_texto_series(equipos[col])

    df = df.dropna(subset=["fecha"])

    return df, equipos


# ==========================================================
# PREPARAR DATA TALLER
# ==========================================================

def preparar_taller():

    df = cargar_lucarbal_taller()

    if df.empty:
        return df

    df = limpiar_columnas(df)

    columnas = [
        "id_taller",
        "fecha",
        "turno",
        "tecnico",
        "apoyo_1",
        "apoyo_2",
        "hora_inicio",
        "hora_fin",
        "tiempo_trabajo_min",
        "tipo_actividad",
        "detalle",
        "estado",
        "evidencia",
        "timestamp_registro"
    ]

    for col in columnas:
        if col not in df.columns:
            df[col] = ""

    df = convertir_fecha(df, "fecha")
    df = convertir_numero(df, "tiempo_trabajo_min")

    # No normalizar evidencia porque malogra el base64
    columnas_no_normalizar = [
        "fecha",
        "tiempo_trabajo_min",
        "evidencia"
    ]

    for col in df.columns:
        if col not in columnas_no_normalizar:
            df[col] = normalizar_texto_series(df[col])

    df = df.dropna(subset=["fecha"])

    return df


# ==========================================================
# KPIS
# ==========================================================

def calcular_kpis(df, equipos, fecha_ini, fecha_fin, turno):

    dias = (fecha_fin - fecha_ini).days + 1

    if dias <= 0:
        dias = 1

    horas_base_equipo = float(
        dias * (12 if turno != "TODOS" else 24)
    )

    resumen = []

    for _, eq in equipos.iterrows():

        codigo = str(eq.get("codigo_lucarbal", "")).strip().upper()
        cognos = str(eq.get("codigo_cognos", "")).strip().upper()
        familia = str(eq.get("familia_equipo", "")).strip().upper()
        marca = str(eq.get("marca", "")).strip().upper()

        df_eq = df[
            df["codigo_lucarbal"] == codigo
        ].copy()

        horas_parada = float(df_eq["tiempo_parada"].sum())
        eventos = int((df_eq["tiempo_parada"] > 0).sum())

        horas_operativas = max(
            horas_base_equipo - horas_parada,
            0
        )

        disponibilidad = (
            (horas_operativas / horas_base_equipo) * 100
            if horas_base_equipo > 0
            else 100
        )

        mttr = horas_parada / eventos if eventos > 0 else 0
        mtbf = horas_operativas / eventos if eventos > 0 else 0

        # Compatibilidad con registros históricos de tres tiempos.
        # En los registros actuales estas columnas llegan vacías y fueron
        # convertidas a 0, por lo que no afectan los KPI de dos horas.
        tiempos_respuesta_validos = df_eq.loc[
            df_eq["tiempo_respuesta"] > 0,
            "tiempo_respuesta"
        ]

        tiempos_reparacion_validos = df_eq.loc[
            df_eq["tiempo_reparacion"] > 0,
            "tiempo_reparacion"
        ]

        tiempo_respuesta_prom = (
            float(tiempos_respuesta_validos.mean())
            if not tiempos_respuesta_validos.empty
            else 0
        )

        tiempo_reparacion_prom = (
            float(tiempos_reparacion_validos.mean())
            if not tiempos_reparacion_validos.empty
            else 0
        )

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
            "MTBF h": round(mtbf, 2),
            "T. respuesta prom h": round(tiempo_respuesta_prom, 2),
            "T. reparación prom h": round(tiempo_reparacion_prom, 2)
        })

    return pd.DataFrame(resumen)


def resumen_por_flota(df_kpi):

    if df_kpi.empty:
        return pd.DataFrame()

    df_flota = df_kpi.groupby(
        "Familia",
        as_index=False
    ).agg({
        "Horas calendario": "sum",
        "Horas parada": "sum",
        "Horas operativas": "sum",
        "Eventos": "sum"
    })

    df_flota["Disponibilidad %"] = (
        (df_flota["Horas operativas"] / df_flota["Horas calendario"]) * 100
    ).round(2)

    df_flota["MTTR h"] = (
        df_flota["Horas parada"] /
        df_flota["Eventos"].replace(0, pd.NA)
    ).fillna(0).round(2)

    df_flota["MTBF h"] = (
        df_flota["Horas operativas"] /
        df_flota["Eventos"].replace(0, pd.NA)
    ).fillna(0).round(2)

    return df_flota


# ==========================================================
# ESTILO TABLAS PDF
# ==========================================================

def estilo_tabla(tabla, font_size=6):

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    return tabla


# ==========================================================
# GENERAR PDF
# ==========================================================

def generar_pdf(
    df_kpi,
    df_flota,
    df_eventos,
    df_taller,
    fecha_ini,
    fecha_fin,
    turno,
    familia,
    incluir_taller,
    incluir_anexo_fotografico
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=18,
        leftMargin=18,
        topMargin=22,
        bottomMargin=22
    )

    styles = getSampleStyleSheet()

    estilo_normal = styles["Normal"]
    estilo_titulo = styles["Title"]
    estilo_h2 = styles["Heading2"]

    estilo_desc = ParagraphStyle(
        "desc",
        parent=styles["Normal"],
        fontSize=5.2,
        leading=6,
        alignment=0
    )

    story = []

    story.append(Paragraph("INFORME KPI LUCARBAL", estilo_titulo))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Periodo: {fecha_ini} al {fecha_fin}", estilo_normal))
    story.append(Paragraph(f"Turno: {turno}", estilo_normal))
    story.append(Paragraph(f"Flota: {familia}", estilo_normal))
    story.append(Paragraph(
        f"Fecha generación: {ahora_peru().strftime('%d/%m/%Y %H:%M')}",
        estilo_normal
    ))
    story.append(Spacer(1, 14))

    # ======================================================
    # 1. RESUMEN POR FLOTA
    # ======================================================

    story.append(Paragraph("1. Resumen ejecutivo por flota", estilo_h2))

    tabla_flota_data = [[
        "Flota",
        "Disp. %",
        "H. parada",
        "Eventos",
        "MTTR",
        "MTBF"
    ]]

    for _, r in df_flota.iterrows():

        tabla_flota_data.append([
            str(r["Familia"]),
            f'{float(r["Disponibilidad %"]):.2f} %',
            f'{float(r["Horas parada"]):.2f}',
            str(int(r["Eventos"])),
            f'{float(r["MTTR h"]):.2f}',
            f'{float(r["MTBF h"]):.2f}'
        ])

    tabla_flota = Table(tabla_flota_data, repeatRows=1)
    tabla_flota = estilo_tabla(tabla_flota, 7)

    story.append(tabla_flota)
    story.append(Spacer(1, 14))

    # ======================================================
    # 2. DISPONIBILIDAD POR EQUIPO
    # ======================================================

    story.append(Paragraph("2. Disponibilidad por equipo", estilo_h2))

    tabla_kpi_data = [[
        "Familia",
        "Equipo",
        "Cognos",
        "Disp. %",
        "H. parada",
        "Eventos",
        "MTTR",
        "MTBF",
        "T. resp.",
        "T. rep."
    ]]

    for _, r in df_kpi.iterrows():

        tabla_kpi_data.append([
            str(r["Familia"])[:16],
            str(r["Equipo"])[:15],
            str(r["Cognos"])[:18],
            f'{float(r["Disponibilidad %"]):.2f} %',
            f'{float(r["Horas parada"]):.2f}',
            str(int(r["Eventos"])),
            f'{float(r["MTTR h"]):.2f}',
            f'{float(r["MTBF h"]):.2f}',
            f'{float(r.get("T. respuesta prom h", 0)):.2f}',
            f'{float(r.get("T. reparación prom h", 0)):.2f}'
        ])

    tabla_kpi = Table(tabla_kpi_data, repeatRows=1)
    tabla_kpi = estilo_tabla(tabla_kpi, 5.8)

    story.append(tabla_kpi)
    story.append(Spacer(1, 14))

    # ======================================================
    # 3. DETALLE DE EVENTOS MINA
    # ======================================================

    story.append(Paragraph("3. Detalle de eventos mina", estilo_h2))

    detalle = [[
        "Fecha",
        "Turno",
        "Equipo",
        "Tipo",
        "Técnico",
        "Inicio Parada",
        "Hora Subsanada",
        "Estado",
        "Descripción"
    ]]

    for _, r in df_eventos.iterrows():

        detalle.append([
            r["fecha"].strftime("%d/%m/%Y") if pd.notna(r["fecha"]) else "",
            str(r.get("turno", ""))[:7],
            str(r.get("codigo_lucarbal", ""))[:13],
            str(r.get("tipo_mantenimiento", ""))[:12],
            str(r.get("tecnico", ""))[:20],
            str(r.get("hora_falla", ""))[:7],
            str(r.get("hora_subsanada", ""))[:7],
            str(r.get("estado_operativo", ""))[:12],
            Paragraph(str(r.get("descripcion", ""))[:220], estilo_desc)
        ])

    tabla_detalle = Table(detalle, repeatRows=1)
    tabla_detalle = estilo_tabla(tabla_detalle, 4.9)

    story.append(tabla_detalle)

    # ======================================================
    # 4. DETALLE TALLER
    # ======================================================

    if incluir_taller:

        story.append(PageBreak())
        story.append(Paragraph("4. Detalle de trabajos de taller", estilo_h2))

        taller_data = [[
            "Fecha",
            "Turno",
            "Técnico",
            "Apoyo 1",
            "Apoyo 2",
            "Inicio",
            "Fin",
            "Min",
            "Estado",
            "Detalle"
        ]]

        for _, r in df_taller.iterrows():

            taller_data.append([
                r["fecha"].strftime("%d/%m/%Y") if pd.notna(r["fecha"]) else "",
                str(r.get("turno", ""))[:8],
                str(r.get("tecnico", ""))[:20],
                str(r.get("apoyo_1", ""))[:16],
                str(r.get("apoyo_2", ""))[:16],
                str(r.get("hora_inicio", ""))[:7],
                str(r.get("hora_fin", ""))[:7],
                f'{float(r.get("tiempo_trabajo_min", 0)):.0f}',
                str(r.get("estado", ""))[:12],
                Paragraph(str(r.get("detalle", ""))[:240], estilo_desc)
            ])

        tabla_taller = Table(taller_data, repeatRows=1)
        tabla_taller = estilo_tabla(tabla_taller, 5)

        story.append(tabla_taller)

    # ======================================================
    # 5. ANEXO FOTOGRÁFICO
    # ======================================================

    if incluir_anexo_fotografico:

        story.append(PageBreak())
        story.append(Paragraph("5. Anexo fotográfico - Eventos mina", estilo_h2))

        eventos_foto = df_eventos[
            df_eventos["foto"].astype(str).str.strip().str.upper() != "SIN FOTO"
        ].copy()

        eventos_foto = eventos_foto[
            eventos_foto["foto"].astype(str).str.strip() != ""
        ].copy()

        if eventos_foto.empty:

            story.append(Paragraph(
                "No se registraron evidencias fotográficas de eventos mina.",
                estilo_normal
            ))

        else:

            for _, r in eventos_foto.iterrows():

                story.append(Spacer(1, 8))

                info = [[
                    "Evento",
                    "Fecha",
                    "Equipo",
                    "Técnico",
                    "Detalle"
                ], [
                    str(r.get("id", "")),
                    r["fecha"].strftime("%d/%m/%Y") if pd.notna(r["fecha"]) else "",
                    str(r.get("codigo_lucarbal", "")),
                    str(r.get("tecnico", ""))[:25],
                    Paragraph(str(r.get("descripcion", ""))[:260], estilo_desc)
                ]]

                tabla_info = Table(
                    info,
                    colWidths=[
                        2.5 * cm,
                        2.5 * cm,
                        3 * cm,
                        4 * cm,
                        14 * cm
                    ]
                )

                tabla_info = estilo_tabla(tabla_info, 5.3)

                story.append(tabla_info)

                img_buffer = extraer_imagen_base64(
                    str(r.get("foto", ""))
                )

                if img_buffer is not None:

                    try:
                        img = Image(
                            img_buffer,
                            width=7.5 * cm,
                            height=5.5 * cm
                        )

                        story.append(Spacer(1, 6))
                        story.append(img)

                    except Exception:

                        story.append(Paragraph(
                            "No se pudo cargar la imagen.",
                            estilo_normal
                        ))

        if incluir_taller:

            story.append(PageBreak())
            story.append(Paragraph(
                "6. Anexo fotográfico - Trabajos de taller",
                estilo_h2
            ))

            taller_foto = df_taller[
                df_taller["evidencia"].astype(str).str.strip().str.upper() != "SIN FOTO"
            ].copy()

            taller_foto = taller_foto[
                taller_foto["evidencia"].astype(str).str.strip() != ""
            ].copy()

            if taller_foto.empty:

                story.append(Paragraph(
                    "No se registraron evidencias fotográficas de trabajos de taller.",
                    estilo_normal
                ))

            else:

                for _, r in taller_foto.iterrows():

                    story.append(Spacer(1, 8))

                    info = [[
                        "ID",
                        "Fecha",
                        "Técnico",
                        "Detalle"
                    ], [
                        str(r.get("id_taller", "")),
                        r["fecha"].strftime("%d/%m/%Y") if pd.notna(r["fecha"]) else "",
                        str(r.get("tecnico", ""))[:25],
                        Paragraph(str(r.get("detalle", ""))[:300], estilo_desc)
                    ]]

                    tabla_info = Table(
                        info,
                        colWidths=[
                            3 * cm,
                            3 * cm,
                            5 * cm,
                            16 * cm
                        ]
                    )

                    tabla_info = estilo_tabla(tabla_info, 5.3)

                    story.append(tabla_info)

                    img_buffer = extraer_imagen_base64(
                        str(r.get("evidencia", ""))
                    )

                    if img_buffer is not None:

                        try:
                            img = Image(
                                img_buffer,
                                width=7.5 * cm,
                                height=5.5 * cm
                            )

                            story.append(Spacer(1, 6))
                            story.append(img)

                        except Exception:

                            story.append(Paragraph(
                                "No se pudo cargar la imagen.",
                                estilo_normal
                            ))

    doc.build(story)

    buffer.seek(0)

    return buffer


# ==========================================================
# DASHBOARD PRINCIPAL
# ==========================================================

def mostrar_dashboard_lucarbal():

    st.title("🚛 Dashboard KPI Lucarbal")
    st.caption(
        "Disponibilidad · MTTR · MTBF · Tiempos de atención · Taller · Informe PDF"
    )

    if st.button("🔄 Actualizar datos", use_container_width=True):
        refrescar_cache_datos()
        st.rerun()

    st.markdown("---")

    df, equipos = preparar_eventos()
    df_taller = preparar_taller()

    if equipos.empty:
        st.warning("No existe catálogo de equipos Lucarbal.")
        return

    if df.empty:
        st.warning("No existen eventos registrados en Lucarbal.")
        return

    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fecha_ini = st.date_input(
            "Fecha inicio",
            value=fecha_min
        )

    with col2:
        fecha_fin = st.date_input(
            "Fecha fin",
            value=fecha_max
        )

    if fecha_fin < fecha_ini:
        st.error("La fecha fin no puede ser menor que la fecha inicio.")
        return

    with col3:
        turno = st.selectbox(
            "Turno",
            [
                "TODOS",
                "DIA",
                "NOCHE"
            ]
        )

    with col4:
        familia = st.selectbox(
            "Flota",
            ["TODAS"] + sorted(
                equipos["familia_equipo"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    col_check1, col_check2 = st.columns(2)

    with col_check1:
        incluir_taller = st.checkbox(
            "Incluir trabajos de taller en informe PDF",
            value=False
        )

    with col_check2:
        incluir_anexo_fotografico = st.checkbox(
            "Incluir anexo fotográfico en informe PDF",
            value=True
        )

    # ======================================================
    # FILTROS EVENTOS
    # ======================================================

    df_filtrado = df[
        (df["fecha"].dt.date >= fecha_ini) &
        (df["fecha"].dt.date <= fecha_fin)
    ].copy()

    df_taller_filtrado = df_taller.copy()

    if not df_taller_filtrado.empty:

        df_taller_filtrado = df_taller_filtrado[
            (df_taller_filtrado["fecha"].dt.date >= fecha_ini) &
            (df_taller_filtrado["fecha"].dt.date <= fecha_fin)
        ].copy()

    if turno != "TODOS":

        df_filtrado = df_filtrado[
            df_filtrado["turno"] == turno
        ].copy()

        if not df_taller_filtrado.empty:

            df_taller_filtrado = df_taller_filtrado[
                df_taller_filtrado["turno"] == turno
            ].copy()

    equipos_filtrados = equipos.copy()

    if familia != "TODAS":

        equipos_filtrados = equipos_filtrados[
            equipos_filtrados["familia_equipo"] == familia
        ].copy()

        df_filtrado = df_filtrado[
            df_filtrado["familia_equipo"] == familia
        ].copy()

    if equipos_filtrados.empty:
        st.warning("No hay equipos en el catálogo con los filtros seleccionados.")
        return

    df_kpi = calcular_kpis(
        df_filtrado,
        equipos_filtrados,
        fecha_ini,
        fecha_fin,
        turno
    )

    df_flota = resumen_por_flota(df_kpi)

    if df_kpi.empty:
        st.warning("No se pudo calcular KPI con la información disponible.")
        return

    # ======================================================
    # KPIS GENERALES
    # ======================================================

    disp_global = float(df_kpi["Disponibilidad %"].mean())
    horas_parada = float(df_kpi["Horas parada"].sum())
    eventos = int(df_kpi["Eventos"].sum())

    mttr_global = horas_parada / eventos if eventos > 0 else 0

    horas_operativas = float(df_kpi["Horas operativas"].sum())

    mtbf_global = horas_operativas / eventos if eventos > 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Disponibilidad promedio",
        f"{disp_global:.2f} %"
    )

    c2.metric(
        "Horas parada",
        f"{horas_parada:.2f} h"
    )

    c3.metric(
        "Eventos",
        eventos
    )

    c4.metric(
        "MTTR estimado",
        f"{mttr_global:.2f} h"
    )

    c5, c6 = st.columns(2)

    c5.metric(
        "MTBF estimado",
        f"{mtbf_global:.2f} h"
    )

    c6.metric(
        "Equipos base",
        len(equipos_filtrados)
    )

    # ======================================================
    # RESUMEN POR FLOTA
    # ======================================================

    st.markdown("---")
    st.subheader("🚛 Resumen ejecutivo por flota")

    st.dataframe(
        df_flota,
        use_container_width=True
    )

    # ======================================================
    # DISPONIBILIDAD POR EQUIPO
    # ======================================================

    st.subheader("📊 Disponibilidad por equipo")

    fig_disp = px.bar(
        df_kpi.sort_values("Disponibilidad %"),
        x="Equipo",
        y="Disponibilidad %",
        color="Familia",
        text="Disponibilidad %",
        hover_data=[
            "Cognos",
            "Horas parada",
            "Eventos",
            "MTTR h",
            "MTBF h"
        ]
    )

    fig_disp.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_disp.update_layout(
        yaxis_range=[0, 105]
    )

    st.plotly_chart(
        fig_disp,
        use_container_width=True
    )

    # ======================================================
    # HORAS PARADA
    # ======================================================

    st.subheader("⏱ Horas de parada por equipo")

    fig_parada = px.bar(
        df_kpi.sort_values("Horas parada", ascending=False),
        x="Equipo",
        y="Horas parada",
        color="Familia",
        text="Horas parada",
        hover_data=[
            "Cognos",
            "Eventos"
        ]
    )

    fig_parada.update_traces(
        texttemplate="%{text:.1f} h",
        textposition="outside"
    )

    st.plotly_chart(
        fig_parada,
        use_container_width=True
    )

    # ======================================================
    # PREVENTIVO VS CORRECTIVO
    # ======================================================

    st.subheader("🔧 Preventivo vs Correctivo")

    if df_filtrado.empty:

        st.info("No hay eventos para graficar.")

    else:

        df_tipo = df_filtrado.groupby(
            "tipo_mantenimiento",
            as_index=False
        ).agg({
            "tiempo_parada": "sum",
            "id": "count"
        }).rename(columns={
            "tiempo_parada": "Horas parada",
            "id": "Eventos"
        })

        fig_tipo = px.bar(
            df_tipo.sort_values("Horas parada", ascending=False),
            x="tipo_mantenimiento",
            y="Horas parada",
            text="Horas parada",
            color="tipo_mantenimiento"
        )

        fig_tipo.update_traces(
            texttemplate="%{text:.1f} h",
            textposition="outside"
        )

        st.plotly_chart(
            fig_tipo,
            use_container_width=True
        )

    # ======================================================
    # KPI POR EQUIPO
    # ======================================================

    st.subheader("📋 KPI por equipo")

    columnas_kpi = [
        "Familia",
        "Marca",
        "Equipo",
        "Cognos",
        "Horas calendario",
        "Horas parada",
        "Horas operativas",
        "Eventos",
        "Disponibilidad %",
        "MTTR h",
        "MTBF h",
        "T. respuesta prom h",
        "T. reparación prom h"
    ]

    # Evita que el dashboard se detenga si una columna opcional no existe
    # en una versión antigua o futura de la hoja de cálculo.
    for col in columnas_kpi:
        if col not in df_kpi.columns:
            df_kpi[col] = 0 if col not in [
                "Familia",
                "Marca",
                "Equipo",
                "Cognos"
            ] else ""

    st.dataframe(
        df_kpi[columnas_kpi],
        use_container_width=True
    )

    # ======================================================
    # DETALLE EVENTOS
    # ======================================================

    st.subheader("🧾 Detalle de eventos mina")

    columnas_eventos = [
        "fecha",
        "turno",
        "codigo_lucarbal",
        "tipo_mantenimiento",
        "tecnico",
        "hora_falla",
        "hora_subsanada",
        "estado_operativo",
        "descripcion"
    ]

    for col in columnas_eventos:
        if col not in df_filtrado.columns:
            df_filtrado[col] = ""

    if df_filtrado.empty:

        st.info("No hay eventos registrados para el filtro seleccionado.")

    else:

        st.dataframe(
            df_filtrado[columnas_eventos].sort_values("fecha"),
            use_container_width=True
        )

    # ======================================================
    # TALLER
    # ======================================================

    if incluir_taller:

        st.subheader("🏭 Trabajos de taller incluidos")

        if df_taller_filtrado.empty:

            st.info("No hay trabajos de taller registrados con los filtros seleccionados.")

        else:

            col_t1, col_t2, col_t3 = st.columns(3)

            total_taller_min = float(
                df_taller_filtrado["tiempo_trabajo_min"].sum()
            )

            total_taller_h = total_taller_min / 60

            col_t1.metric(
                "Actividades taller",
                len(df_taller_filtrado)
            )

            col_t2.metric(
                "Horas taller",
                f"{total_taller_h:.2f} h"
            )

            col_t3.metric(
                "Minutos taller",
                f"{total_taller_min:.0f} min"
            )

            columnas_taller = [
                "fecha",
                "turno",
                "tecnico",
                "apoyo_1",
                "apoyo_2",
                "hora_inicio",
                "hora_fin",
                "tiempo_trabajo_min",
                "estado",
                "detalle"
            ]

            for col in columnas_taller:
                if col not in df_taller_filtrado.columns:
                    df_taller_filtrado[col] = ""

            st.dataframe(
                df_taller_filtrado[columnas_taller].sort_values("fecha"),
                use_container_width=True
            )

    # ======================================================
    # EXPORTAR PDF
    # ======================================================

    st.markdown("---")

    pdf = generar_pdf(
        df_kpi=df_kpi,
        df_flota=df_flota,
        df_eventos=df_filtrado,
        df_taller=df_taller_filtrado,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
        turno=turno,
        familia=familia,
        incluir_taller=incluir_taller,
        incluir_anexo_fotografico=incluir_anexo_fotografico
    )

    st.download_button(
        label="📄 Exportar informe PDF",
        data=pdf,
        file_name=f"Informe_Lucarbal_{fecha_ini}_{fecha_fin}_{turno}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
