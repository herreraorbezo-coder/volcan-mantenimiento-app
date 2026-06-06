# ==========================================================
# DASHBOARD.PY
# DASHBOARD / HISTORIAL DE EVENTOS - VOLCAN APP
# ==========================================================

import streamlit as st
import pandas as pd
import altair as alt
import base64

from io import BytesIO
from datetime import datetime

import matplotlib.pyplot as plt
from PIL import Image as PILImage

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    Image as RLImage
)

from database import cargar_bitacora, cargar_equipos


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


def preparar_equipos_por_nivel():

    df_equipos = cargar_equipos()

    if df_equipos.empty:
        return {}

    df_equipos.columns = df_equipos.columns.str.strip().str.lower()

    if "nivel" not in df_equipos.columns or "codigo" not in df_equipos.columns:
        return {}

    df_equipos["nivel"] = df_equipos["nivel"].astype(str).str.strip()
    df_equipos["codigo"] = df_equipos["codigo"].astype(str).str.strip()

    return (
        df_equipos
        .drop_duplicates(subset=["nivel", "codigo"])
        .groupby("nivel")["codigo"]
        .nunique()
        .to_dict()
    )


def crear_tabla_pdf(data, headers, font_size=7, col_widths=None):

    tabla_data = [headers] + data

    tabla = Table(
        tabla_data,
        repeatRows=1,
        colWidths=col_widths
    )

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B71C1C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ]
        )
    )

    return tabla


def crear_imagen_pdf_desde_bytes(imagen_bytes, max_width=11.5 * cm, max_height=6.8 * cm):

    try:
        img_buffer = BytesIO(imagen_bytes)

        with PILImage.open(BytesIO(imagen_bytes)) as img:
            ancho_px, alto_px = img.size

        if ancho_px <= 0 or alto_px <= 0:
            return None

        escala = min(
            max_width / ancho_px,
            max_height / alto_px
        )

        ancho_final = ancho_px * escala
        alto_final = alto_px * escala

        imagen_pdf = RLImage(
            img_buffer,
            width=ancho_final,
            height=alto_final
        )
        imagen_pdf.hAlign = "CENTER"

        return imagen_pdf

    except Exception:
        return None


def grafico_pdf_disponibilidad(df_pdf, equipos_por_nivel, fecha_inicio, fecha_fin):

    if df_pdf.empty:
        return None

    df = df_pdf.copy()
    df["fecha_dia"] = df["fecha"].dt.date

    niveles = sorted(df["nivel"].dropna().unique().tolist())
    fechas = pd.date_range(fecha_inicio, fecha_fin, freq="D").date

    fig, ax1 = plt.subplots(figsize=(12, 5.8))

    ancho = 0.75 / max(len(niveles), 1)

    for i, nv in enumerate(niveles):

        df_nv = df[df["nivel"] == nv].copy()
        cantidad_bombas = equipos_por_nivel.get(nv, 1)

        data = []

        for fecha in fechas:

            horas_parada = df_nv[df_nv["fecha_dia"] == fecha]["tiempo_parada"].sum()
            horas_programadas_dia = cantidad_bombas * 24
            dm = (
                ((horas_programadas_dia - horas_parada) / horas_programadas_dia) * 100
                if horas_programadas_dia > 0
                else 0
            )
            dm = max(0, min(dm, 100))
            data.append(dm)

        posiciones = list(range(len(fechas)))
        posiciones_ajustadas = [p + (i * ancho) for p in posiciones]

        barras = ax1.bar(
            posiciones_ajustadas,
            data,
            width=ancho,
            label=f"Nivel {nv}",
            edgecolor="black",
            linewidth=0.8
        )

        # RÓTULOS DE %DM EN CADA BARRA
        for barra in barras:
            altura = barra.get_height()

            ax1.text(
                barra.get_x() + barra.get_width() / 2,
                altura + 1.4,
                f"{altura:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.75,
                    pad=1.0
                )
            )

    ax1.set_title(
        "Disponibilidad Mecánica por Nivel",
        fontsize=15,
        fontweight="bold",
        pad=14
    )
    ax1.set_xlabel("Fecha", fontsize=11)
    ax1.set_ylabel("% Disponibilidad mecánica", fontsize=11)
    ax1.set_ylim(0, 112)
    ax1.set_xticks([p + (ancho * (len(niveles) - 1) / 2) for p in range(len(fechas))])
    ax1.set_xticklabels([pd.to_datetime(f).strftime("%d/%m") for f in fechas])
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()

    fallas_por_fecha = (
        df.groupby("fecha_dia")
        .size()
        .reindex(fechas, fill_value=0)
    )

    ax2.plot(
        range(len(fechas)),
        fallas_por_fecha.values,
        marker="o",
        markersize=7,
        linewidth=2.5,
        color="crimson",
        markerfacecolor="white",
        markeredgecolor="black",
        markeredgewidth=1.2,
        label="Cantidad de fallas"
    )

    # RÓTULOS DE CANTIDAD DE FALLAS EN CADA PUNTO
    for x_pos, valor in enumerate(fallas_por_fecha.values):

        ax2.annotate(
            str(int(valor)),
            (x_pos, valor),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            bbox=dict(
                facecolor="white",
                edgecolor="black",
                linewidth=0.3,
                alpha=0.85,
                pad=1.5
            )
        )

    ax2.set_ylabel("Cantidad de fallas", fontsize=11)
    ax2.set_ylim(0, max(fallas_por_fecha.max() + 1, 2))

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=4,
        frameon=True,
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.08, 1, 1])

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170)
    plt.close(fig)
    buffer.seek(0)

    return buffer


def grafico_pdf_paradas(df_pdf, fecha_inicio, fecha_fin):

    if df_pdf.empty:
        return None

    df = df_pdf.copy()
    df["fecha_dia"] = df["fecha"].dt.date

    niveles = sorted(df["nivel"].dropna().unique().tolist())
    fechas = pd.date_range(fecha_inicio, fecha_fin, freq="D").date

    fig, ax = plt.subplots(figsize=(12, 5.8))

    ancho = 0.75 / max(len(niveles), 1)

    max_horas = 0

    for i, nv in enumerate(niveles):

        df_nv = df[df["nivel"] == nv].copy()

        data = []

        for fecha in fechas:
            horas = df_nv[df_nv["fecha_dia"] == fecha]["tiempo_parada"].sum()
            data.append(horas)

        if data:
            max_horas = max(max_horas, max(data))

        posiciones = list(range(len(fechas)))
        posiciones_ajustadas = [p + (i * ancho) for p in posiciones]

        barras = ax.bar(
            posiciones_ajustadas,
            data,
            width=ancho,
            label=f"Nivel {nv}",
            edgecolor="black",
            linewidth=0.8
        )

        # RÓTULOS DE HORAS DE PARADA
        for barra in barras:

            altura = barra.get_height()

            if altura > 0:

                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    altura + max(max_horas * 0.02, 0.08),
                    f"{altura:.1f} h",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    bbox=dict(
                        facecolor="white",
                        edgecolor="none",
                        alpha=0.75,
                        pad=1.0
                    )
                )

    ax.set_title(
        "Tiempo de Paradas por Nivel",
        fontsize=15,
        fontweight="bold",
        pad=14
    )
    ax.set_xlabel("Fecha", fontsize=11)
    ax.set_ylabel("Horas de parada", fontsize=11)
    ax.set_xticks([p + (ancho * (len(niveles) - 1) / 2) for p in range(len(fechas))])
    ax.set_xticklabels([pd.to_datetime(f).strftime("%d/%m") for f in fechas])
    ax.set_ylim(0, max(max_horas * 1.22, 1))
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=4,
        frameon=True,
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.08, 1, 1])

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170)
    plt.close(fig)
    buffer.seek(0)

    return buffer


def grafico_pdf_preventivo_correctivo(df_pdf, fecha_inicio, fecha_fin):

    if df_pdf.empty:
        return None

    df = df_pdf.copy()
    df["fecha_dia"] = df["fecha"].dt.date

    fechas = pd.date_range(fecha_inicio, fecha_fin, freq="D").date

    preventivo = []
    correctivo = []

    for fecha in fechas:

        df_fecha = df[df["fecha_dia"] == fecha]

        preventivo.append(
            df_fecha[df_fecha["tipo_mantenimiento"].str.upper() == "PREVENTIVO"]["tiempo_parada"].sum()
        )

        correctivo.append(
            df_fecha[df_fecha["tipo_mantenimiento"].str.upper() == "CORRECTIVO"]["tiempo_parada"].sum()
        )

    fig, ax1 = plt.subplots(figsize=(12, 5.8))

    x = list(range(len(fechas)))

    barras_prev = ax1.bar(
        x,
        preventivo,
        label="Horas preventivas",
        edgecolor="black",
        linewidth=0.8
    )

    max_prev = max(preventivo) if preventivo else 0
    max_corr = max(correctivo) if correctivo else 0

    # RÓTULOS DE HORAS PREVENTIVAS
    for barra in barras_prev:

        altura = barra.get_height()

        if altura > 0:

            ax1.text(
                barra.get_x() + barra.get_width() / 2,
                altura + max(max_prev * 0.03, 0.05),
                f"{altura:.1f} h",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.75,
                    pad=1.0
                )
            )

    ax1.set_title(
        "Trabajos Preventivos vs Correctivos",
        fontsize=15,
        fontweight="bold",
        pad=14
    )
    ax1.set_xlabel("Fecha", fontsize=11)
    ax1.set_ylabel("Horas preventivas", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels([pd.to_datetime(f).strftime("%d/%m") for f in fechas])
    ax1.set_ylim(0, max(max_prev * 1.25, 1))
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()

    ax2.plot(
        x,
        correctivo,
        marker="o",
        markersize=7,
        linewidth=2.5,
        color="crimson",
        markerfacecolor="white",
        markeredgecolor="black",
        markeredgewidth=1.2,
        label="Horas correctivas"
    )

    # RÓTULOS DE HORAS CORRECTIVAS
    for x_pos, valor in enumerate(correctivo):

        if valor > 0:

            ax2.annotate(
                f"{valor:.1f} h",
                (x_pos, valor),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontsize=8,
                fontweight="bold",
                bbox=dict(
                    facecolor="white",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=0.85,
                    pad=1.5
                )
            )

    ax2.set_ylabel("Horas correctivas", fontsize=11)
    ax2.set_ylim(0, max(max_corr * 1.25, 1))

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=2,
        frameon=True,
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.08, 1, 1])

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=170)
    plt.close(fig)
    buffer.seek(0)

    return buffer


def generar_pdf_informe_bombeo(df_informe, equipos_por_nivel, fecha_inicio, fecha_fin, incluir_fotos=False):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.0 * cm,
        leftMargin=1.0 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloVolcan",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#B71C1C"),
        spaceAfter=12
    )

    subtitulo_style = ParagraphStyle(
        "SubtituloVolcan",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#212121"),
        spaceBefore=10,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalVolcan",
        parent=styles["Normal"],
        fontSize=9,
        leading=12
    )

    detalle_style = ParagraphStyle(
        "Detalle",
        parent=styles["Normal"],
        fontSize=6,
        leading=8
    )

    elementos = []

    fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")

    elementos.append(
        Paragraph(
            "INFORME SEMANAL DEL SISTEMA DE BOMBEO",
            titulo_style
        )
    )

    elementos.append(
        Paragraph(
            f"Periodo evaluado: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
            normal_style
        )
    )

    elementos.append(
        Paragraph(
            f"Fecha de emisión: {fecha_emision}",
            normal_style
        )
    )

    elementos.append(Spacer(1, 10))

    texto_intro = """
    Estimados,<br/><br/>
    Se adjunta el informe semanal del sistema de bombeo correspondiente al periodo seleccionado.
    El presente reporte consolida la disponibilidad mecánica por nivel, horas de parada,
    distribución de trabajos preventivos y correctivos, así como el detalle de intervenciones
    ejecutadas en campo.
    """

    elementos.append(Paragraph(texto_intro, normal_style))
    elementos.append(Spacer(1, 10))

    if df_informe.empty:

        elementos.append(
            Paragraph(
                "No se registran eventos para el periodo seleccionado.",
                normal_style
            )
        )

    else:

        df_pdf = df_informe.copy()
        df_pdf["fecha_dia"] = df_pdf["fecha"].dt.date

        dias_periodo = (fecha_fin - fecha_inicio).days + 1
        total_eventos = len(df_pdf)
        total_horas = df_pdf["tiempo_parada"].sum()

        total_correctivo = df_pdf[
            df_pdf["tipo_mantenimiento"].str.upper() == "CORRECTIVO"
        ]["tiempo_parada"].sum()

        total_preventivo = df_pdf[
            df_pdf["tipo_mantenimiento"].str.upper() == "PREVENTIVO"
        ]["tiempo_parada"].sum()

        niveles = sorted(df_pdf["nivel"].dropna().unique().tolist())

        total_hp = 0

        for nv in niveles:
            total_hp += equipos_por_nivel.get(nv, 1) * 24 * dias_periodo

        dm_global = (
            ((total_hp - total_horas) / total_hp) * 100
            if total_hp > 0
            else 0
        )

        dm_global = max(0, min(dm_global, 100))

        elementos.append(Paragraph("1. Resumen ejecutivo", subtitulo_style))

        resumen_data = [
            ["Eventos registrados", str(total_eventos)],
            ["Horas de parada", f"{total_horas:.2f} h"],
            ["Horas preventivas", f"{total_preventivo:.2f} h"],
            ["Horas correctivas", f"{total_correctivo:.2f} h"],
            ["Disponibilidad mecánica global", f"{dm_global:.2f} %"],
        ]

        elementos.append(
            crear_tabla_pdf(
                resumen_data,
                ["Indicador", "Valor"],
                font_size=8
            )
        )

        elementos.append(Spacer(1, 12))

        grafico_dm = grafico_pdf_disponibilidad(
            df_pdf,
            equipos_por_nivel,
            fecha_inicio,
            fecha_fin
        )

        if grafico_dm is not None:
            elementos.append(
                KeepTogether([
                    Paragraph("2. Gráfico de disponibilidad mecánica", subtitulo_style),
                    RLImage(grafico_dm, width=24 * cm, height=8.2 * cm),
                    Spacer(1, 6)
                ])
            )

        elementos.append(Paragraph("3. Disponibilidad mecánica por nivel", subtitulo_style))

        dm_nivel_data = []

        for nv in niveles:

            df_nv = df_pdf[df_pdf["nivel"] == nv].copy()

            horas_parada_nv = df_nv["tiempo_parada"].sum()
            cant_fallas_nv = len(df_nv)
            cant_bombas_nv = equipos_por_nivel.get(nv, 1)

            hp_nv = cant_bombas_nv * 24 * dias_periodo

            dm_nv = (
                ((hp_nv - horas_parada_nv) / hp_nv) * 100
                if hp_nv > 0
                else 0
            )

            dm_nv = max(0, min(dm_nv, 100))

            dm_nivel_data.append(
                [
                    nv,
                    str(cant_bombas_nv),
                    f"{hp_nv:.2f}",
                    f"{horas_parada_nv:.2f}",
                    str(cant_fallas_nv),
                    f"{dm_nv:.2f} %"
                ]
            )

        elementos.append(
            crear_tabla_pdf(
                dm_nivel_data,
                ["Nivel", "Bombas", "Horas Prog.", "Horas parada", "Cant. fallas", "%DM"],
                font_size=7
            )
        )

        elementos.append(PageBreak())

        grafico_paradas = grafico_pdf_paradas(
            df_pdf,
            fecha_inicio,
            fecha_fin
        )

        if grafico_paradas is not None:
            elementos.append(
                KeepTogether([
                    Paragraph("4. Gráfico de tiempo de paradas", subtitulo_style),
                    RLImage(grafico_paradas, width=24 * cm, height=8.2 * cm),
                    Spacer(1, 6)
                ])
            )

        elementos.append(Paragraph("5. Tiempo de paradas por nivel y fecha", subtitulo_style))

        df_paradas = (
            df_pdf
            .groupby(["nivel", "fecha_dia"])["tiempo_parada"]
            .sum()
            .reset_index()
        )

        paradas_data = []

        for _, row in df_paradas.iterrows():
            paradas_data.append(
                [
                    str(row["nivel"]),
                    pd.to_datetime(row["fecha_dia"]).strftime("%d/%m/%Y"),
                    f"{row['tiempo_parada']:.2f}"
                ]
            )

        elementos.append(
            crear_tabla_pdf(
                paradas_data,
                ["Nivel", "Fecha", "Horas de parada"],
                font_size=7
            )
        )

        elementos.append(PageBreak())

        grafico_pc = grafico_pdf_preventivo_correctivo(
            df_pdf,
            fecha_inicio,
            fecha_fin
        )

        if grafico_pc is not None:
            elementos.append(
                KeepTogether([
                    Paragraph("6. Gráfico preventivo vs correctivo", subtitulo_style),
                    RLImage(grafico_pc, width=24 * cm, height=8.2 * cm),
                    Spacer(1, 6)
                ])
            )

        elementos.append(Paragraph("7. Trabajos preventivos vs correctivos", subtitulo_style))

        df_pc = (
            df_pdf
            .pivot_table(
                index=["nivel", "fecha_dia"],
                columns="tipo_mantenimiento",
                values="tiempo_parada",
                aggfunc="sum",
                fill_value=0
            )
            .reset_index()
        )

        for col in ["PREVENTIVO", "CORRECTIVO"]:
            if col not in df_pc.columns:
                df_pc[col] = 0

        pc_data = []

        for _, row in df_pc.iterrows():
            pc_data.append(
                [
                    str(row["nivel"]),
                    pd.to_datetime(row["fecha_dia"]).strftime("%d/%m/%Y"),
                    f"{row['PREVENTIVO']:.2f}",
                    f"{row['CORRECTIVO']:.2f}"
                ]
            )

        elementos.append(
            crear_tabla_pdf(
                pc_data,
                ["Nivel", "Fecha", "Horas preventivo", "Horas correctivo"],
                font_size=7
            )
        )

        elementos.append(PageBreak())

        elementos.append(Paragraph("8. Detalle de intervenciones", subtitulo_style))

        df_detalle = df_pdf[
            [
                "fecha",
                "nivel",
                "codigo",
                "hora_falla",
                "hora_subsanada",
                "descripcion"
            ]
        ].copy()

        df_detalle["fecha"] = df_detalle["fecha"].dt.strftime("%d/%m/%Y")

        detalle_data = []

        for _, row in df_detalle.iterrows():

            descripcion = Paragraph(
                str(row["descripcion"]),
                detalle_style
            )

            detalle_data.append(
                [
                    row["fecha"],
                    str(row["nivel"]),
                    str(row["codigo"]),
                    str(row["hora_falla"]),
                    str(row["hora_subsanada"]),
                    descripcion
                ]
            )

        elementos.append(
            crear_tabla_pdf(
                detalle_data,
                ["FECHA", "NV", "CODIGO DE BOMBA", "TIEMPO INIC", "TIEMPO FIN", "DETALLE DE TRABAJO"],
                font_size=6,
                col_widths=[
                    2.2 * cm,
                    1.5 * cm,
                    3.2 * cm,
                    2.0 * cm,
                    2.0 * cm,
                    16.0 * cm
                ]
            )
        )

        # ==================================================
        # 9. ANEXO FOTOGRÁFICO
        # ==================================================

        if incluir_fotos and "foto" in df_pdf.columns:

            df_fotos = df_pdf[
                df_pdf["foto"].astype(str).str.contains("base64", na=False)
            ].copy()

            if not df_fotos.empty:

                elementos.append(PageBreak())
                elementos.append(Paragraph("9. Anexo fotográfico", subtitulo_style))
                elementos.append(
                    Paragraph(
                        "Se adjuntan las evidencias fotográficas registradas para las intervenciones del periodo evaluado.",
                        normal_style
                    )
                )
                elementos.append(Spacer(1, 8))

                for _, row in df_fotos.iterrows():

                    imagen_bytes = obtener_bytes_imagen(row.get("foto", ""))

                    if imagen_bytes is None:
                        continue

                    fecha_txt = ""
                    try:
                        fecha_txt = pd.to_datetime(row.get("fecha")).strftime("%d/%m/%Y")
                    except Exception:
                        fecha_txt = str(row.get("fecha", ""))

                    descripcion_txt = str(row.get("descripcion", ""))

                    descripcion_parrafo = Paragraph(
                        descripcion_txt,
                        detalle_style
                    )

                    tabla_evento = crear_tabla_pdf(
                        data=[
                            [
                                str(row.get("id", "")),
                                fecha_txt,
                                str(row.get("nivel", "")),
                                str(row.get("codigo", "")),
                                descripcion_parrafo
                            ]
                        ],
                        headers=[
                            "EVENTO",
                            "FECHA",
                            "NV",
                            "CÓDIGO DE BOMBA",
                            "DETALLE / TRABAJO"
                        ],
                        font_size=6,
                        col_widths=[
                            2.5 * cm,
                            2.3 * cm,
                            2.0 * cm,
                            3.3 * cm,
                            15.2 * cm
                        ]
                    )

                    imagen_pdf = crear_imagen_pdf_desde_bytes(
                        imagen_bytes,
                        max_width=12.5 * cm,
                        max_height=6.8 * cm
                    )

                    if imagen_pdf is None:
                        elementos.append(
                            KeepTogether([
                                tabla_evento,
                                Spacer(1, 6),
                                Paragraph(
                                    "No se pudo insertar la evidencia fotográfica de este evento.",
                                    normal_style
                                ),
                                Spacer(1, 10)
                            ])
                        )
                    else:
                        elementos.append(
                            KeepTogether([
                                tabla_evento,
                                Spacer(1, 6),
                                imagen_pdf,
                                Spacer(1, 12)
                            ])
                        )

    doc.build(elementos)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf



# ==========================================================
# WORD / DOCX
# ==========================================================

def set_cell_background(cell, fill):

    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False, font_size=8, font_color="000000"):

    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor.from_string(font_color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def agregar_parrafo_word(documento, texto, font_size=9, bold=False, color="000000", align="left"):

    parrafo = documento.add_paragraph()

    if align == "center":
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT

    run = parrafo.add_run(str(texto))
    run.bold = bold
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor.from_string(color)

    return parrafo


def agregar_titulo_word(documento, texto, nivel=1):

    parrafo = documento.add_paragraph()
    run = parrafo.add_run(str(texto))
    run.bold = True

    if nivel == 0:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(183, 28, 28)
    else:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0, 0, 0)

    return parrafo


def set_cell_width(cell, width_inches):

    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")

    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)

    tc_w.set(qn("w:w"), str(int(width_inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def agregar_tabla_word(
    documento,
    headers,
    data,
    font_size=8,
    column_widths=None,
    detalle_izquierda=True
):

    tabla = documento.add_table(
        rows=1,
        cols=len(headers)
    )

    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"
    tabla.autofit = False
    tabla.allow_autofit = False

    # ======================================================
    # ENCABEZADOS
    # ======================================================

    header_cells = tabla.rows[0].cells

    for idx, header in enumerate(headers):

        if column_widths and idx < len(column_widths):
            set_cell_width(header_cells[idx], column_widths[idx])
            header_cells[idx].width = Inches(column_widths[idx])

        set_cell_background(header_cells[idx], "B71C1C")

        set_cell_text(
            header_cells[idx],
            header,
            bold=True,
            font_size=font_size,
            font_color="FFFFFF"
        )

    # ======================================================
    # CUERPO DE TABLA
    # ======================================================

    for row_data in data:

        row = tabla.add_row()
        cells = row.cells

        for idx, value in enumerate(row_data):

            cell = cells[idx]

            if column_widths and idx < len(column_widths):
                set_cell_width(cell, column_widths[idx])
                cell.width = Inches(column_widths[idx])

            cell.text = ""

            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0

            # La última columna normalmente es descripción/detalle.
            if detalle_izquierda and idx == len(row_data) - 1:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run = paragraph.add_run(str(value))
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor.from_string("000000")

            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        # Color alternado por fila
        if len(tabla.rows) % 2 == 0:
            for cell in row.cells:
                set_cell_background(cell, "F5F5F5")

    documento.add_paragraph()

    return tabla


def agregar_imagen_word(documento, imagen_buffer, width_inches=8.8):

    try:
        imagen_buffer.seek(0)
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run()
        run.add_picture(imagen_buffer, width=Inches(width_inches))
    except Exception:
        agregar_parrafo_word(
            documento,
            "No se pudo insertar la imagen en el informe Word.",
            font_size=8
        )


def generar_word_informe_bombeo(df_informe, equipos_por_nivel, fecha_inicio, fecha_fin, incluir_fotos=False):

    documento = Document()

    section = documento.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11.69)
    section.page_height = Inches(8.27)
    section.top_margin = Inches(0.45)
    section.bottom_margin = Inches(0.45)
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)

    fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")

    agregar_titulo_word(
        documento,
        "INFORME SEMANAL DEL SISTEMA DE BOMBEO",
        nivel=0
    )

    agregar_parrafo_word(
        documento,
        f"Periodo evaluado: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
        font_size=9
    )

    agregar_parrafo_word(
        documento,
        f"Fecha de emisión: {fecha_emision}",
        font_size=9
    )

    agregar_parrafo_word(
        documento,
        "Estimados,",
        font_size=9
    )

    agregar_parrafo_word(
        documento,
        "Se adjunta el informe semanal del sistema de bombeo correspondiente al periodo seleccionado. "
        "El presente reporte consolida la disponibilidad mecánica por nivel, horas de parada, "
        "distribución de trabajos preventivos y correctivos, así como el detalle de intervenciones ejecutadas en campo.",
        font_size=9
    )

    if df_informe.empty:
        agregar_parrafo_word(
            documento,
            "No se registran eventos para el periodo seleccionado.",
            font_size=9,
            bold=True
        )

        buffer = BytesIO()
        documento.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    df_word = df_informe.copy()
    df_word["fecha_dia"] = df_word["fecha"].dt.date

    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    total_eventos = len(df_word)
    total_horas = df_word["tiempo_parada"].sum()

    total_correctivo = df_word[
        df_word["tipo_mantenimiento"].str.upper() == "CORRECTIVO"
    ]["tiempo_parada"].sum()

    total_preventivo = df_word[
        df_word["tipo_mantenimiento"].str.upper() == "PREVENTIVO"
    ]["tiempo_parada"].sum()

    niveles = sorted(df_word["nivel"].dropna().unique().tolist())

    total_hp = 0

    for nv in niveles:
        total_hp += equipos_por_nivel.get(nv, 1) * 24 * dias_periodo

    dm_global = (
        ((total_hp - total_horas) / total_hp) * 100
        if total_hp > 0
        else 0
    )

    dm_global = max(0, min(dm_global, 100))

    agregar_titulo_word(documento, "1. Resumen ejecutivo", nivel=1)

    agregar_tabla_word(
        documento,
        ["Indicador", "Valor"],
        [
            ["Eventos registrados", str(total_eventos)],
            ["Horas de parada", f"{total_horas:.2f} h"],
            ["Horas preventivas", f"{total_preventivo:.2f} h"],
            ["Horas correctivas", f"{total_correctivo:.2f} h"],
            ["Disponibilidad mecánica global", f"{dm_global:.2f} %"],
        ],
        font_size=8
    )

    grafico_dm = grafico_pdf_disponibilidad(
        df_word,
        equipos_por_nivel,
        fecha_inicio,
        fecha_fin
    )

    if grafico_dm is not None:
        agregar_titulo_word(documento, "2. Gráfico de disponibilidad mecánica", nivel=1)
        agregar_imagen_word(documento, grafico_dm, width_inches=8.8)

    agregar_titulo_word(documento, "3. Disponibilidad mecánica por nivel", nivel=1)

    dm_nivel_data = []

    for nv in niveles:

        df_nv = df_word[df_word["nivel"] == nv].copy()
        horas_parada_nv = df_nv["tiempo_parada"].sum()
        cant_fallas_nv = len(df_nv)
        cant_bombas_nv = equipos_por_nivel.get(nv, 1)
        hp_nv = cant_bombas_nv * 24 * dias_periodo

        dm_nv = (
            ((hp_nv - horas_parada_nv) / hp_nv) * 100
            if hp_nv > 0
            else 0
        )

        dm_nv = max(0, min(dm_nv, 100))

        dm_nivel_data.append(
            [
                nv,
                str(cant_bombas_nv),
                f"{hp_nv:.2f}",
                f"{horas_parada_nv:.2f}",
                str(cant_fallas_nv),
                f"{dm_nv:.2f} %"
            ]
        )

    agregar_tabla_word(
        documento,
        ["Nivel", "Bombas", "Horas Prog.", "Horas parada", "Cant. fallas", "%DM"],
        dm_nivel_data,
        font_size=7
    )

    grafico_paradas = grafico_pdf_paradas(
        df_word,
        fecha_inicio,
        fecha_fin
    )

    if grafico_paradas is not None:
        agregar_titulo_word(documento, "4. Gráfico de tiempo de paradas", nivel=1)
        agregar_imagen_word(documento, grafico_paradas, width_inches=8.8)

    agregar_titulo_word(documento, "5. Tiempo de paradas por nivel y fecha", nivel=1)

    df_paradas = (
        df_word
        .groupby(["nivel", "fecha_dia"])["tiempo_parada"]
        .sum()
        .reset_index()
    )

    paradas_data = []

    for _, row in df_paradas.iterrows():
        paradas_data.append(
            [
                str(row["nivel"]),
                pd.to_datetime(row["fecha_dia"]).strftime("%d/%m/%Y"),
                f"{row['tiempo_parada']:.2f}"
            ]
        )

    agregar_tabla_word(
        documento,
        ["Nivel", "Fecha", "Horas de parada"],
        paradas_data,
        font_size=7
    )

    grafico_pc = grafico_pdf_preventivo_correctivo(
        df_word,
        fecha_inicio,
        fecha_fin
    )

    if grafico_pc is not None:
        agregar_titulo_word(documento, "6. Gráfico preventivo vs correctivo", nivel=1)
        agregar_imagen_word(documento, grafico_pc, width_inches=8.8)

    agregar_titulo_word(documento, "7. Trabajos preventivos vs correctivos", nivel=1)

    df_pc = (
        df_word
        .pivot_table(
            index=["nivel", "fecha_dia"],
            columns="tipo_mantenimiento",
            values="tiempo_parada",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    for col in ["PREVENTIVO", "CORRECTIVO"]:
        if col not in df_pc.columns:
            df_pc[col] = 0

    pc_data = []

    for _, row in df_pc.iterrows():
        pc_data.append(
            [
                str(row["nivel"]),
                pd.to_datetime(row["fecha_dia"]).strftime("%d/%m/%Y"),
                f"{row['PREVENTIVO']:.2f}",
                f"{row['CORRECTIVO']:.2f}"
            ]
        )

    agregar_tabla_word(
        documento,
        ["Nivel", "Fecha", "Horas preventivo", "Horas correctivo"],
        pc_data,
        font_size=7
    )

    agregar_titulo_word(documento, "8. Detalle de intervenciones", nivel=1)

    df_detalle = df_word[
        [
            "fecha",
            "nivel",
            "codigo",
            "hora_falla",
            "hora_subsanada",
            "descripcion"
        ]
    ].copy()

    df_detalle["fecha"] = df_detalle["fecha"].dt.strftime("%d/%m/%Y")

    detalle_data = []

    for _, row in df_detalle.iterrows():
        detalle_data.append(
            [
                row["fecha"],
                str(row["nivel"]),
                str(row["codigo"]),
                str(row["hora_falla"]),
                str(row["hora_subsanada"]),
                str(row["descripcion"])
            ]
        )

    agregar_tabla_word(
        documento,
        ["FECHA", "NV", "CÓDIGO DE BOMBA", "TIEMPO INIC", "TIEMPO FIN", "DETALLE DE TRABAJO"],
        detalle_data,
        font_size=7,
        column_widths=[
            1.05,  # FECHA
            1.00,  # NV
            1.30,  # CÓDIGO
            0.95,  # TIEMPO INIC
            0.95,  # TIEMPO FIN
            5.75   # DETALLE DE TRABAJO
        ],
        detalle_izquierda=True
    )

    if incluir_fotos and "foto" in df_word.columns:

        df_fotos = df_word[
            df_word["foto"].astype(str).str.contains("base64", na=False)
        ].copy()

        if not df_fotos.empty:

            agregar_titulo_word(documento, "9. Anexo fotográfico", nivel=1)
            agregar_parrafo_word(
                documento,
                "Se adjuntan las evidencias fotográficas registradas para las intervenciones del periodo evaluado.",
                font_size=9
            )

            for _, row in df_fotos.iterrows():

                imagen_bytes = obtener_bytes_imagen(row.get("foto", ""))

                if imagen_bytes is None:
                    continue

                try:
                    fecha_txt = pd.to_datetime(row.get("fecha")).strftime("%d/%m/%Y")
                except Exception:
                    fecha_txt = str(row.get("fecha", ""))

                descripcion_txt = str(row.get("descripcion", ""))

                agregar_tabla_word(
                    documento,
                    ["EVENTO", "FECHA", "NV", "CÓDIGO DE BOMBA", "DETALLE / TRABAJO"],
                    [
                        [
                            str(row.get("id", "")),
                            fecha_txt,
                            str(row.get("nivel", "")),
                            str(row.get("codigo", "")),
                            descripcion_txt
                        ]
                    ],
                    font_size=7,
                    column_widths=[
                        1.25,  # EVENTO
                        1.05,  # FECHA
                        0.90,  # NV
                        1.30,  # CÓDIGO
                        6.50   # DETALLE / TRABAJO
                    ],
                    detalle_izquierda=True
                )

                imagen_pdf = crear_imagen_pdf_desde_bytes(
                    imagen_bytes,
                    max_width=10.5 * cm,
                    max_height=6.0 * cm
                )

                if imagen_pdf is not None:
                    imagen_buffer = BytesIO(imagen_bytes)
                    agregar_imagen_word(documento, imagen_buffer, width_inches=3.8)

    buffer = BytesIO()
    documento.save(buffer)
    buffer.seek(0)

    return buffer.getvalue()


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
        "apoyo_1",
        "apoyo_2",
        "sistema",
        "tipo_mantenimiento",
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
        "tipo_mantenimiento",
        "tipo_falla",
        "causa_preliminar",
        "repuesto_requerido",
        "estado",
        "tecnico",
        "apoyo_1",
        "apoyo_2"
    ]:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.warning("No hay fechas válidas en la bitácora.")
        return

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

    colf5, colf6, colf7, colf8 = st.columns(4)

    with colf5:
        estado = st.selectbox(
            "Estado",
            ["TODOS"] + sorted(df["estado"].dropna().unique().tolist())
        )

    with colf6:
        tipo_mantenimiento = st.selectbox(
            "Tipo mantenimiento",
            ["TODOS"] + sorted(df["tipo_mantenimiento"].dropna().unique().tolist())
        )

    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    with colf7:
        fecha_inicio = st.date_input(
            "Fecha inicio",
            value=fecha_min
        )

    with colf8:
        fecha_fin = st.date_input(
            "Fecha fin",
            value=fecha_max
        )

    equipos_por_nivel = preparar_equipos_por_nivel()

    df_informe = df[
        (df["fecha"].dt.date >= fecha_inicio) &
        (df["fecha"].dt.date <= fecha_fin)
    ].copy()

    st.markdown("---")

    st.header("📄 Informe Semanal - Sistema de Bombeo")
    st.caption("Este botón exporta el informe formal en PDF según el rango de fechas seleccionado.")

    incluir_fotos_pdf = st.checkbox(
        "Incluir anexo fotográfico en el PDF",
        value=False,
        help="Activa esta opción solo cuando necesites sustentar el informe con evidencias. El PDF será más pesado."
    )

    pdf_bytes = generar_pdf_informe_bombeo(
        df_informe=df_informe,
        equipos_por_nivel=equipos_por_nivel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        incluir_fotos=incluir_fotos_pdf
    )

    st.download_button(
        label="📄 Exportar informe semanal PDF",
        data=pdf_bytes,
        file_name=f"informe_bombeo_{fecha_inicio}_{fecha_fin}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    word_bytes = generar_word_informe_bombeo(
        df_informe=df_informe,
        equipos_por_nivel=equipos_por_nivel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        incluir_fotos=incluir_fotos_pdf
    )

    st.download_button(
        label="📝 Exportar informe Word",
        data=word_bytes,
        file_name=f"informe_bombeo_{fecha_inicio}_{fecha_fin}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

    st.markdown("---")

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

    if tipo_mantenimiento != "TODOS":
        df_filtrado = df_filtrado[
            df_filtrado["tipo_mantenimiento"] == tipo_mantenimiento
        ]

    if df_filtrado.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

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

    st.subheader("📈 Análisis gráfico gerencial")

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
            color=alt.Color("codigo:N", legend=None),
            tooltip=[
                "codigo",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_top_bombas, use_container_width=True)

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
            color=alt.Color("tipo_falla:N", legend=None),
            tooltip=["tipo_falla", "cantidad"]
        )
    )

    st.altair_chart(chart_pareto_falla, use_container_width=True)

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
            color=alt.Color("causa_preliminar:N", legend=None),
            tooltip=["causa_preliminar", "cantidad"]
        )
    )

    st.altair_chart(chart_pareto_causa, use_container_width=True)

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
                color=alt.Color("repuesto_requerido:N", legend=None),
                tooltip=["repuesto_requerido", "cantidad"]
            )
        )

        st.altair_chart(chart_repuestos, use_container_width=True)

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
            color=alt.Color("nivel:N", legend=None),
            tooltip=[
                "nivel",
                alt.Tooltip("tiempo_parada:Q", format=".2f")
            ]
        )
    )

    st.altair_chart(chart_horas_nivel, use_container_width=True)

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
            color=alt.Color("tecnico:N", legend=None),
            tooltip=["tecnico", "eventos"]
        )
    )

    st.altair_chart(chart_tecnico, use_container_width=True)

    st.markdown("### 8. Horas preventivas vs correctivas")

    df_tipo_mantto = (
        df_filtrado
        .groupby("tipo_mantenimiento")["tiempo_parada"]
        .sum()
        .reset_index()
        .sort_values("tiempo_parada", ascending=False)
    )

    if df_tipo_mantto.empty:
        st.info("No hay datos de tipo de mantenimiento para graficar.")
    else:
        chart_tipo_mantto = (
            alt.Chart(df_tipo_mantto)
            .mark_bar()
            .encode(
                x=alt.X("tipo_mantenimiento:N", title="Tipo mantenimiento"),
                y=alt.Y("tiempo_parada:Q", title="Horas"),
                color=alt.Color("tipo_mantenimiento:N", legend=None),
                tooltip=[
                    "tipo_mantenimiento",
                    alt.Tooltip("tiempo_parada:Q", format=".2f")
                ]
            )
        )

        st.altair_chart(chart_tipo_mantto, use_container_width=True)

    st.markdown("### 9. Tendencia diaria de eventos")

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

    st.subheader("📋 Historial de Eventos")

    columnas_mostrar = [
        "id",
        "fecha",
        "tecnico",
        "apoyo_1",
        "apoyo_2",
        "nivel",
        "ubicacion",
        "codigo",
        "tipo_mantenimiento",
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

    csv = df_tabla.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Descargar historial CSV",
        data=csv,
        file_name="historial_eventos_bombeo.csv",
        mime="text/csv"
    )
