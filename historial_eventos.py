# ==========================================================
# HISTORIAL_EVENTOS.PY
# REPOSITORIO VISUAL DE EVENTOS - SISTEMA DE BOMBEO
# Incluye opcionalmente actividades de Taller / Apoyo VOLCAN
# ==========================================================

import base64
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import (
    cargar_bitacora,
    cargar_volcan_taller,
    refrescar_cache_datos,
)


VALORES_VACIOS = {"", "nan", "none", "sin foto", "nat"}


def obtener_base64_limpio(foto_base64):
    """Devuelve únicamente el contenido base64 válido de una fotografía."""
    if not isinstance(foto_base64, str):
        return None

    foto_base64 = foto_base64.strip()
    if foto_base64.lower() in VALORES_VACIOS:
        return None

    if "base64," in foto_base64:
        foto_base64 = foto_base64.split("base64,", 1)[1]

    try:
        base64.b64decode(foto_base64, validate=True)
        return foto_base64
    except Exception:
        return None


def limpiar_texto(valor, defecto="N/D"):
    """Limpia valores vacíos y escapa HTML para evitar errores en tarjetas."""
    if valor is None:
        return defecto

    texto = str(valor).strip()
    if texto.lower() in VALORES_VACIOS:
        return defecto

    return html.escape(texto)


def normalizar_columnas(df):
    """Normaliza encabezados procedentes de Google Sheets."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace("á", "a", regex=False)
        .str.replace("é", "e", regex=False)
        .str.replace("í", "i", regex=False)
        .str.replace("ó", "o", regex=False)
        .str.replace("ú", "u", regex=False)
        .str.replace("ñ", "n", regex=False)
    )
    return df


def primera_columna(df, alternativas, defecto=""):
    """Obtiene una serie usando el primer encabezado disponible."""
    for columna in alternativas:
        if columna in df.columns:
            return df[columna]
    return pd.Series([defecto] * len(df), index=df.index, dtype="object")


def preparar_eventos_bombeo(df):
    """Convierte la hoja bitácora al formato común del repositorio."""
    df = normalizar_columnas(df)
    if df.empty:
        return pd.DataFrame()

    salida = pd.DataFrame(index=df.index)
    salida["id"] = primera_columna(df, ["id", "id_evento"])
    salida["fecha"] = pd.to_datetime(
        primera_columna(df, ["fecha", "fecha_evento"]), errors="coerce"
    )
    salida["nivel"] = primera_columna(df, ["nivel"])
    salida["ubicacion"] = primera_columna(df, ["ubicacion", "labor"])
    salida["codigo"] = primera_columna(df, ["codigo", "codigo_bomba", "equipo"])
    salida["hora_inicio"] = primera_columna(df, ["hora_falla", "hora_inicio"])
    salida["hora_fin"] = primera_columna(df, ["hora_subsanada", "hora_fin"])
    salida["tipo_mantenimiento"] = primera_columna(
        df, ["tipo_mantenimiento", "mantenimiento"]
    )
    salida["tipo_intervencion"] = primera_columna(
        df, ["tipo_falla", "falla", "intervencion"]
    )
    salida["causa"] = primera_columna(df, ["causa_preliminar", "causa"])
    salida["descripcion"] = primera_columna(
        df, ["descripcion", "detalle", "trabajo_realizado"]
    )
    salida["estado"] = primera_columna(df, ["estado", "estado_operativo"])
    salida["tecnico"] = primera_columna(df, ["tecnico", "tecnico_principal"])
    salida["apoyo_1"] = primera_columna(df, ["apoyo_1"])
    salida["apoyo_2"] = primera_columna(df, ["apoyo_2"])
    salida["empresa_area"] = "SISTEMA DE BOMBEO"
    salida["foto"] = primera_columna(df, ["foto", "evidencia"])
    salida["tipo_registro"] = "EVENTO DE BOMBEO"
    salida["orden_registro"] = pd.to_datetime(
        primera_columna(df, ["fecha_registro"]), errors="coerce"
    )

    return salida.dropna(subset=["fecha"])


def preparar_taller_volcan(df):
    """Convierte la hoja volcan_taller al formato común del repositorio."""
    df = normalizar_columnas(df)
    if df.empty:
        return pd.DataFrame()

    salida = pd.DataFrame(index=df.index)
    salida["id"] = primera_columna(df, ["id_taller", "id"])
    salida["fecha"] = pd.to_datetime(
        primera_columna(df, ["fecha", "fecha_actividad"]), errors="coerce"
    )
    salida["nivel"] = "TALLER"
    salida["ubicacion"] = primera_columna(df, ["area_apoyo", "area", "ubicacion"])
    salida["codigo"] = "TALLER / APOYO"
    salida["hora_inicio"] = primera_columna(df, ["hora_inicio"])
    salida["hora_fin"] = primera_columna(df, ["hora_fin"])
    salida["tipo_mantenimiento"] = primera_columna(
        df, ["tipo_actividad", "actividad"], defecto="ACTIVIDAD DE TALLER"
    )
    salida["tipo_mantenimiento"] = salida["tipo_mantenimiento"].replace(
        {"": "ACTIVIDAD DE TALLER"}
    )
    salida["tipo_intervencion"] = "TALLER / APOYO OPERATIVO"
    salida["causa"] = primera_columna(
        df, ["empresa_apoyada", "empresa", "contrata"], defecto="VOLCAN"
    )
    salida["descripcion"] = primera_columna(df, ["detalle", "descripcion"])
    salida["estado"] = primera_columna(df, ["estado"])
    salida["tecnico"] = primera_columna(df, ["tecnico", "tecnico_principal"])
    salida["apoyo_1"] = primera_columna(df, ["apoyo_1"])
    salida["apoyo_2"] = primera_columna(df, ["apoyo_2"])

    empresa = primera_columna(
        df, ["empresa_apoyada", "empresa", "contrata"], defecto="VOLCAN"
    ).astype(str).str.strip()
    area = primera_columna(df, ["area_apoyo", "area"], defecto="TALLER").astype(str).str.strip()
    salida["empresa_area"] = empresa + " · " + area

    salida["foto"] = primera_columna(df, ["evidencia", "foto"])
    salida["tipo_registro"] = "ACTIVIDAD DE TALLER / APOYO"
    salida["orden_registro"] = pd.to_datetime(
        primera_columna(df, ["fecha_registro"]), errors="coerce"
    )

    return salida.dropna(subset=["fecha"])


def color_estado(estado):
    estado = str(estado).upper().strip()

    if any(x in estado for x in ["SUBSANADO", "FINALIZADO", "OPERATIVO"]):
        return "#2E7D32"
    if any(x in estado for x in ["PENDIENTE", "PROCESO"]):
        return "#F57C00"
    if any(x in estado for x in ["FUERA", "INOPERATIVO"]):
        return "#C62828"
    if "SEGUIMIENTO" in estado:
        return "#1565C0"
    return "#616161"


def construir_apoyos(row):
    apoyos = []
    for columna in ["apoyo_1", "apoyo_2"]:
        valor = str(row.get(columna, "")).strip()
        if valor.lower() not in VALORES_VACIOS and valor.upper() != "SIN APOYO":
            apoyos.append(valor)
    return " · ".join(apoyos) if apoyos else "Sin apoyo registrado"


def mostrar_tarjeta(row):
    evento = limpiar_texto(row.get("id", ""))
    fecha = row["fecha"].strftime("%d/%m/%Y")
    nivel = limpiar_texto(row.get("nivel", ""))
    ubicacion = limpiar_texto(row.get("ubicacion", ""))
    codigo = limpiar_texto(row.get("codigo", ""))
    hora_inicio = limpiar_texto(row.get("hora_inicio", ""))
    hora_fin = limpiar_texto(row.get("hora_fin", ""))
    tipo_mantenimiento = limpiar_texto(row.get("tipo_mantenimiento", ""))
    tipo_intervencion = limpiar_texto(row.get("tipo_intervencion", ""))
    causa = limpiar_texto(row.get("causa", ""))
    descripcion = limpiar_texto(
        row.get("descripcion", ""), "Sin descripción registrada."
    )
    estado = limpiar_texto(row.get("estado", ""))
    tecnico = limpiar_texto(row.get("tecnico", ""))
    tipo_registro = limpiar_texto(row.get("tipo_registro", ""))
    empresa_area = limpiar_texto(row.get("empresa_area", ""))
    apoyos = limpiar_texto(construir_apoyos(row))
    foto_base64 = obtener_base64_limpio(row.get("foto", ""))

    color = color_estado(estado)
    es_taller = "TALLER" in str(row.get("tipo_registro", "")).upper()
    color_borde = "#00A6D6" if es_taller else "#F2B705"
    icono = "🏭" if es_taller else "⚙️"

    if foto_base64:
        bloque_imagen = f"""
        <div class="image-box">
            <img src="data:image/jpeg;base64,{foto_base64}">
            <div class="image-caption">{codigo} · {evento}</div>
        </div>
        """
    else:
        bloque_imagen = """
        <div class="no-image">📷<br>Sin evidencia</div>
        """

    html_card = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin:0; padding:0; font-family:Arial,sans-serif; background:transparent; }}
        .container {{ display:grid; grid-template-columns:240px minmax(0,1fr); gap:18px; margin-bottom:18px; width:100%; }}
        .image-box, .no-image {{ background:#151515; border-radius:14px; border:1px solid rgba(255,255,255,.12); height:260px; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:10px; box-shadow:0 8px 20px rgba(0,0,0,.30); }}
        .image-box img {{ max-width:220px; max-height:205px; object-fit:contain; border-radius:10px; }}
        .image-caption {{ color:#d0d0d0; font-size:12px; margin-top:8px; text-align:center; }}
        .no-image {{ border-style:dashed; color:#9e9e9e; font-weight:700; text-align:center; }}
        .repo-card {{ background:linear-gradient(135deg,#1d1d1d 0%,#2a2a2a 100%); border-radius:16px; padding:16px 18px; border-left:7px solid {color_borde}; box-shadow:0 10px 28px rgba(0,0,0,.35); min-height:260px; }}
        .repo-header {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:8px; }}
        .repo-equipo {{ font-size:28px; font-weight:900; color:#fff; letter-spacing:.4px; }}
        .repo-subtitle {{ color:#bdbdbd; font-size:13px; margin-top:3px; }}
        .badges {{ display:flex; flex-direction:column; gap:7px; align-items:flex-end; }}
        .badge {{ color:#fff; padding:7px 13px; border-radius:20px; font-weight:800; font-size:12px; text-align:center; white-space:nowrap; }}
        .tipo {{ background:{color_borde}; color:#111; }}
        .repo-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:12px 0 14px; }}
        .repo-box {{ background:rgba(255,255,255,.07); border-radius:10px; padding:10px; min-width:0; }}
        .repo-label {{ color:#9e9e9e; font-size:11px; font-weight:700; margin-bottom:3px; text-transform:uppercase; }}
        .repo-value {{ color:#fff; font-size:14px; font-weight:800; overflow-wrap:anywhere; }}
        .repo-section-title {{ color:{color_borde}; font-size:13px; font-weight:900; margin-top:8px; margin-bottom:4px; text-transform:uppercase; }}
        .repo-text {{ color:#eee; font-size:14px; line-height:1.42; overflow-wrap:anywhere; }}
        .repo-footer {{ margin-top:12px; color:#bdbdbd; font-size:12px; }}
        @media (max-width:700px) {{
            .container {{ grid-template-columns:1fr; }}
            .image-box, .no-image {{ height:220px; }}
            .repo-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
            .repo-header {{ flex-direction:column; }}
            .badges {{ flex-direction:row; flex-wrap:wrap; align-items:flex-start; }}
        }}
    </style>
    </head>
    <body>
        <div class="container">
            {bloque_imagen}
            <div class="repo-card">
                <div class="repo-header">
                    <div>
                        <div class="repo-equipo">{icono} {codigo}</div>
                        <div class="repo-subtitle">{evento} · {fecha} · {nivel} · {ubicacion}</div>
                    </div>
                    <div class="badges">
                        <div class="badge tipo">{tipo_registro}</div>
                        <div class="badge" style="background:{color};">{estado}</div>
                    </div>
                </div>
                <div class="repo-grid">
                    <div class="repo-box"><div class="repo-label">Inicio</div><div class="repo-value">{hora_inicio}</div></div>
                    <div class="repo-box"><div class="repo-label">Fin</div><div class="repo-value">{hora_fin}</div></div>
                    <div class="repo-box"><div class="repo-label">Actividad / mantenimiento</div><div class="repo-value">{tipo_mantenimiento}</div></div>
                    <div class="repo-box"><div class="repo-label">Área / empresa</div><div class="repo-value">{empresa_area}</div></div>
                </div>
                <div class="repo-section-title">Trabajo realizado</div>
                <div class="repo-text">{descripcion}</div>
                <div class="repo-section-title">Falla / intervención</div>
                <div class="repo-text">{tipo_intervencion}</div>
                <div class="repo-section-title">Causa / empresa apoyada</div>
                <div class="repo-text">{causa}</div>
                <div class="repo-footer">Registrado por: <b>{tecnico}</b> · Apoyos: <b>{apoyos}</b></div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html_card, height=335, scrolling=False)


def mostrar_historial_eventos():
    st.title("🗂️ Repositorio Visual de Eventos")
    st.caption("Sistema de bombeo · Consulta rápida para cambio de guardia")

    if st.button("🔄 Actualizar datos", use_container_width=True, key="actualizar_historial_bombeo"):
        refrescar_cache_datos()
        st.rerun()

    incluir_taller = st.checkbox(
        "🏭 Incluir actividades de Taller / Apoyo VOLCAN",
        value=False,
        help=(
            "Al marcar esta opción se incorporan al repositorio los trabajos registrados "
            "en la hoja volcan_taller. Desmarcado muestra únicamente eventos de bombeo."
        ),
        key="incluir_taller_historial_bombeo",
    )

    st.markdown("---")

    df_eventos = preparar_eventos_bombeo(cargar_bitacora())
    marcos = [df_eventos] if not df_eventos.empty else []

    if incluir_taller:
        df_taller = preparar_taller_volcan(cargar_volcan_taller())
        if not df_taller.empty:
            marcos.append(df_taller)

    if not marcos:
        st.warning("No existen registros disponibles.")
        return

    df = pd.concat(marcos, ignore_index=True, sort=False)

    columnas_texto = [
        "id", "nivel", "ubicacion", "codigo", "hora_inicio", "hora_fin",
        "tipo_mantenimiento", "tipo_intervencion", "causa", "descripcion",
        "estado", "tecnico", "apoyo_1", "apoyo_2", "empresa_area", "foto",
        "tipo_registro",
    ]
    for columna in columnas_texto:
        if columna not in df.columns:
            df[columna] = ""
        df[columna] = df[columna].fillna("").astype(str).str.strip()

    df = df.dropna(subset=["fecha"])
    if df.empty:
        st.warning("No hay registros con fecha válida.")
        return

    # ======================================================
    # FILTROS
    # ======================================================
    col1, col2, col3, col4 = st.columns(4)

    niveles = sorted(v for v in df["nivel"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)
    codigos = sorted(v for v in df["codigo"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)
    estados = sorted(v for v in df["estado"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)

    with col1:
        nivel = st.selectbox("Nivel / origen", ["TODOS"] + niveles, key="filtro_nivel_hist_bombeo")
    with col2:
        codigo = st.selectbox("Código / actividad", ["TODOS"] + codigos, key="filtro_codigo_hist_bombeo")
    with col3:
        estado = st.selectbox("Estado", ["TODOS"] + estados, key="filtro_estado_hist_bombeo")
    with col4:
        rango = st.selectbox(
            "Periodo",
            ["Últimos 7 días", "Últimos 15 días", "Últimos 30 días", "Todo"],
            key="filtro_periodo_hist_bombeo",
        )

    df_filtrado = df.copy()

    if nivel != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel]
    if codigo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["codigo"] == codigo]
    if estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado]

    if rango != "Todo" and not df_filtrado.empty:
        dias = {"Últimos 7 días": 7, "Últimos 15 días": 15, "Últimos 30 días": 30}[rango]
        fecha_max = df_filtrado["fecha"].max()
        fecha_min = fecha_max - pd.Timedelta(days=dias - 1)
        df_filtrado = df_filtrado[df_filtrado["fecha"] >= fecha_min]

    if df_filtrado.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

    df_filtrado["orden_registro"] = pd.to_datetime(
        df_filtrado.get("orden_registro"), errors="coerce"
    )
    df_filtrado = df_filtrado.sort_values(
        ["fecha", "orden_registro"], ascending=[False, False], na_position="last"
    )

    total_bombeo = int((df_filtrado["tipo_registro"] == "EVENTO DE BOMBEO").sum())
    total_taller = int((df_filtrado["tipo_registro"] == "ACTIVIDAD DE TALLER / APOYO").sum())

    mensaje = f"Registros encontrados: **{len(df_filtrado)}** · Bombeo: **{total_bombeo}**"
    if incluir_taller:
        mensaje += f" · Taller / apoyo: **{total_taller}**"
    mensaje += " · ordenado del más reciente al más antiguo."
    st.info(mensaje)

    st.markdown("---")

    for _, row in df_filtrado.iterrows():
        mostrar_tarjeta(row)
