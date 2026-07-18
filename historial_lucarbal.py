# ==========================================================
# HISTORIAL_LUCARBAL.PY
# REPOSITORIO VISUAL DE EVENTOS - LUCARBAL
# Incluye opcionalmente actividades de Taller LUCARBAL
# ==========================================================

import base64
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import (
    cargar_lucarbal_eventos,
    cargar_lucarbal_taller,
    refrescar_cache_datos,
)


VALORES_VACIOS = {"", "nan", "none", "sin foto", "nat"}


def obtener_base64_limpio(foto_base64):
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
    if valor is None:
        return defecto

    texto = str(valor).strip()
    if texto.lower() in VALORES_VACIOS:
        return defecto

    return html.escape(texto)


def normalizar_columnas(df):
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
    for columna in alternativas:
        if columna in df.columns:
            return df[columna]
    return pd.Series([defecto] * len(df), index=df.index, dtype="object")


def preparar_eventos_lucarbal(df):
    df = normalizar_columnas(df)
    if df.empty:
        return pd.DataFrame()

    salida = pd.DataFrame(index=df.index)
    salida["id"] = primera_columna(df, ["id", "id_evento"])
    salida["fecha"] = pd.to_datetime(primera_columna(df, ["fecha"]), errors="coerce")
    salida["turno"] = primera_columna(df, ["turno"])
    salida["familia"] = primera_columna(df, ["familia_equipo", "familia"])
    salida["equipo"] = primera_columna(df, ["codigo_lucarbal", "equipo"])
    salida["codigo_cognos"] = primera_columna(df, ["codigo_cognos"])
    salida["marca"] = primera_columna(df, ["marca"])
    salida["tipo_mantenimiento"] = primera_columna(df, ["tipo_mantenimiento"])
    salida["hora_inicio"] = primera_columna(df, ["hora_falla", "hora_inicio"])
    salida["hora_fin"] = primera_columna(df, ["hora_subsanada", "hora_fin"])
    salida["tiempo"] = primera_columna(df, ["tiempo_parada", "tiempo_total"])
    salida["descripcion"] = primera_columna(df, ["descripcion", "detalle"])
    salida["estado"] = primera_columna(df, ["estado_operativo", "estado"])
    salida["tecnico"] = primera_columna(df, ["tecnico"])
    salida["apoyo_1"] = primera_columna(df, ["apoyo_1"])
    salida["apoyo_2"] = primera_columna(df, ["apoyo_2"])
    salida["repuesto"] = primera_columna(df, ["detalle_repuesto", "repuesto"])
    salida["foto"] = primera_columna(df, ["foto", "evidencia"])
    salida["tipo_registro"] = "EVENTO EN EQUIPO"
    salida["orden_registro"] = pd.to_datetime(
        primera_columna(df, ["fecha_registro"]), errors="coerce"
    )

    return salida.dropna(subset=["fecha"])


def preparar_taller_lucarbal(df):
    df = normalizar_columnas(df)
    if df.empty:
        return pd.DataFrame()

    salida = pd.DataFrame(index=df.index)
    salida["id"] = primera_columna(df, ["id_taller", "id"])
    salida["fecha"] = pd.to_datetime(primera_columna(df, ["fecha"]), errors="coerce")
    salida["turno"] = primera_columna(df, ["turno"])
    salida["familia"] = "TALLER"
    salida["equipo"] = "TALLER LUCARBAL"
    salida["codigo_cognos"] = "ACTIVIDAD INTERNA"
    salida["marca"] = "LUCARBAL"
    salida["tipo_mantenimiento"] = primera_columna(
        df, ["tipo_actividad", "actividad"], defecto="ACTIVIDAD DE TALLER"
    )
    salida["tipo_mantenimiento"] = salida["tipo_mantenimiento"].replace(
        {"": "ACTIVIDAD DE TALLER"}
    )
    salida["hora_inicio"] = primera_columna(df, ["hora_inicio"])
    salida["hora_fin"] = primera_columna(df, ["hora_fin"])

    tiempo_h = primera_columna(df, ["tiempo_trabajo_h", "tiempo_horas"])
    tiempo_min = primera_columna(df, ["tiempo_trabajo_min", "tiempo_min"])
    salida["tiempo"] = tiempo_h
    mascara_vacia = salida["tiempo"].astype(str).str.strip().str.lower().isin(VALORES_VACIOS)
    salida.loc[mascara_vacia, "tiempo"] = tiempo_min.loc[mascara_vacia].astype(str).apply(
        lambda x: f"{x} min" if x.strip().lower() not in VALORES_VACIOS else ""
    )

    salida["descripcion"] = primera_columna(df, ["detalle", "descripcion"])
    salida["estado"] = primera_columna(df, ["estado"])
    salida["tecnico"] = primera_columna(df, ["tecnico"])
    salida["apoyo_1"] = primera_columna(df, ["apoyo_1"])
    salida["apoyo_2"] = primera_columna(df, ["apoyo_2"])
    salida["repuesto"] = "NO APLICA"
    salida["foto"] = primera_columna(df, ["evidencia", "foto"])
    salida["tipo_registro"] = "TRABAJO DE TALLER"
    salida["orden_registro"] = pd.to_datetime(
        primera_columna(df, ["fecha_registro"]), errors="coerce"
    )

    return salida.dropna(subset=["fecha"])


def color_estado(estado):
    estado = str(estado).upper().strip()
    if any(x in estado for x in ["OPERATIVO", "FINALIZADO", "SUBSANADO"]):
        return "#2E7D32"
    if any(x in estado for x in ["INOPERATIVO", "FUERA"]):
        return "#C62828"
    if any(x in estado for x in ["STAND", "PENDIENTE", "PROCESO"]):
        return "#F57C00"
    return "#616161"


def color_mantenimiento(tipo):
    tipo = str(tipo).upper().strip()
    if "PREVENTIVO" in tipo:
        return "#1565C0"
    if "CORRECTIVO" in tipo:
        return "#C62828"
    if "TALLER" in tipo:
        return "#0086B3"
    return "#616161"


def construir_apoyos(row):
    apoyos = []
    for columna in ["apoyo_1", "apoyo_2"]:
        valor = str(row.get(columna, "")).strip()
        if valor.lower() not in VALORES_VACIOS and valor.upper() != "SIN APOYO":
            apoyos.append(valor)
    return " · ".join(apoyos) if apoyos else "Sin apoyo registrado"


def formatear_tiempo(valor):
    texto = str(valor).strip()
    if texto.lower() in VALORES_VACIOS:
        return "N/D"

    try:
        numero = float(texto.replace(",", "."))
        return f"{numero:.2f} h"
    except Exception:
        return html.escape(texto)


def mostrar_tarjeta(row):
    evento = limpiar_texto(row.get("id", ""))
    fecha = row["fecha"].strftime("%d/%m/%Y")
    turno = limpiar_texto(row.get("turno", ""))
    familia = limpiar_texto(row.get("familia", ""))
    equipo = limpiar_texto(row.get("equipo", ""))
    codigo_cognos = limpiar_texto(row.get("codigo_cognos", ""))
    marca = limpiar_texto(row.get("marca", ""))
    tipo_mantenimiento = limpiar_texto(row.get("tipo_mantenimiento", ""))
    hora_inicio = limpiar_texto(row.get("hora_inicio", ""))
    hora_fin = limpiar_texto(row.get("hora_fin", ""))
    tiempo = formatear_tiempo(row.get("tiempo", ""))
    descripcion = limpiar_texto(row.get("descripcion", ""), "Sin detalle registrado.")
    estado = limpiar_texto(row.get("estado", ""))
    tecnico = limpiar_texto(row.get("tecnico", ""))
    repuesto = limpiar_texto(row.get("repuesto", ""), "No registrado")
    tipo_registro = limpiar_texto(row.get("tipo_registro", ""))
    apoyos = limpiar_texto(construir_apoyos(row))
    foto_base64 = obtener_base64_limpio(row.get("foto", ""))

    color_est = color_estado(estado)
    color_mant = color_mantenimiento(tipo_mantenimiento)
    es_taller = "TALLER" in str(row.get("tipo_registro", "")).upper()
    color_borde = "#00A6D6" if es_taller else "#F2B705"
    icono = "🏭" if es_taller else "🚛"

    if foto_base64:
        bloque_imagen = f"""
        <div class="image-box">
            <img src="data:image/jpeg;base64,{foto_base64}">
            <div class="image-caption">{equipo} · {evento}</div>
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
        * {{ box-sizing:border-box; }}
        body {{ margin:0; padding:0; font-family:Arial,sans-serif; background:transparent; }}
        .container {{ display:grid; grid-template-columns:240px minmax(0,1fr); gap:18px; margin-bottom:18px; width:100%; }}
        .image-box,.no-image {{ background:#151515; border-radius:14px; border:1px solid rgba(255,255,255,.12); height:260px; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:10px; box-shadow:0 8px 20px rgba(0,0,0,.30); }}
        .image-box img {{ max-width:220px; max-height:205px; object-fit:contain; border-radius:10px; }}
        .image-caption {{ color:#d0d0d0; font-size:12px; margin-top:8px; text-align:center; }}
        .no-image {{ border-style:dashed; color:#9e9e9e; font-weight:700; text-align:center; }}
        .repo-card {{ background:linear-gradient(135deg,#1d1d1d 0%,#2a2a2a 100%); border-radius:16px; padding:16px 18px; border-left:7px solid {color_borde}; box-shadow:0 10px 28px rgba(0,0,0,.35); min-height:260px; }}
        .repo-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px; }}
        .repo-equipo {{ font-size:28px; font-weight:900; color:#fff; letter-spacing:.4px; }}
        .repo-subtitle {{ color:#bdbdbd; font-size:13px; margin-top:3px; }}
        .badges {{ display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }}
        .badge {{ color:#fff; padding:7px 13px; border-radius:20px; font-weight:800; font-size:12px; white-space:nowrap; }}
        .tipo-registro {{ background:{color_borde}; color:#111; }}
        .repo-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:12px 0 14px; }}
        .repo-box {{ background:rgba(255,255,255,.07); border-radius:10px; padding:10px; min-width:0; }}
        .repo-label {{ color:#9e9e9e; font-size:11px; font-weight:700; margin-bottom:3px; text-transform:uppercase; }}
        .repo-value {{ color:#fff; font-size:14px; font-weight:800; overflow-wrap:anywhere; }}
        .repo-section-title {{ color:{color_borde}; font-size:13px; font-weight:900; margin-top:8px; margin-bottom:4px; text-transform:uppercase; }}
        .repo-text {{ color:#eee; font-size:14px; line-height:1.42; overflow-wrap:anywhere; }}
        .repo-footer {{ margin-top:12px; color:#bdbdbd; font-size:12px; }}
        @media (max-width:700px) {{
            .container {{ grid-template-columns:1fr; }}
            .image-box,.no-image {{ height:220px; }}
            .repo-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
            .repo-header {{ flex-direction:column; }}
            .badges {{ justify-content:flex-start; }}
        }}
    </style>
    </head>
    <body>
        <div class="container">
            {bloque_imagen}
            <div class="repo-card">
                <div class="repo-header">
                    <div>
                        <div class="repo-equipo">{icono} {equipo}</div>
                        <div class="repo-subtitle">{evento} · {fecha} · {turno} · {familia} · {marca}</div>
                    </div>
                    <div class="badges">
                        <div class="badge tipo-registro">{tipo_registro}</div>
                        <div class="badge" style="background:{color_mant};">{tipo_mantenimiento}</div>
                        <div class="badge" style="background:{color_est};">{estado}</div>
                    </div>
                </div>
                <div class="repo-grid">
                    <div class="repo-box"><div class="repo-label">Cognos / referencia</div><div class="repo-value">{codigo_cognos}</div></div>
                    <div class="repo-box"><div class="repo-label">Inicio</div><div class="repo-value">{hora_inicio}</div></div>
                    <div class="repo-box"><div class="repo-label">Fin</div><div class="repo-value">{hora_fin}</div></div>
                    <div class="repo-box"><div class="repo-label">Tiempo</div><div class="repo-value">{tiempo}</div></div>
                </div>
                <div class="repo-section-title">Descripción de falla / trabajo realizado</div>
                <div class="repo-text">{descripcion}</div>
                <div class="repo-section-title">Repuesto requerido / detalle</div>
                <div class="repo-text">{repuesto}</div>
                <div class="repo-footer">Registrado por: <b>{tecnico}</b> · Apoyos: <b>{apoyos}</b></div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html_card, height=335, scrolling=False)


def mostrar_historial_lucarbal():
    st.title("🚛 Historial Visual Lucarbal")
    st.caption("Volquetes · Minicargadores · Semitrailers · Consulta rápida para cambio de guardia")

    if st.button("🔄 Actualizar datos", use_container_width=True, key="actualizar_historial_lucarbal"):
        refrescar_cache_datos()
        st.rerun()

    incluir_taller = st.checkbox(
        "🏭 Incluir trabajos de Taller LUCARBAL",
        value=False,
        help=(
            "Al marcar esta opción se incorporan los registros de la hoja lucarbal_taller. "
            "Desmarcado muestra únicamente eventos asociados a equipos."
        ),
        key="incluir_taller_historial_lucarbal",
    )

    st.markdown("---")

    df_eventos = preparar_eventos_lucarbal(cargar_lucarbal_eventos())
    marcos = [df_eventos] if not df_eventos.empty else []

    if incluir_taller:
        df_taller = preparar_taller_lucarbal(cargar_lucarbal_taller())
        if not df_taller.empty:
            marcos.append(df_taller)

    if not marcos:
        st.warning("No existen registros Lucarbal disponibles.")
        return

    df = pd.concat(marcos, ignore_index=True, sort=False)

    columnas_texto = [
        "id", "turno", "familia", "equipo", "codigo_cognos", "marca",
        "tipo_mantenimiento", "hora_inicio", "hora_fin", "tiempo", "descripcion",
        "estado", "tecnico", "apoyo_1", "apoyo_2", "repuesto", "foto", "tipo_registro",
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
    col1, col2, col3, col4, col5 = st.columns(5)

    familias = sorted(v for v in df["familia"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)
    equipos = sorted(v for v in df["equipo"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)
    turnos = sorted(v for v in df["turno"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)
    estados = sorted(v for v in df["estado"].unique().tolist() if v and v.lower() not in VALORES_VACIOS)

    with col1:
        familia = st.selectbox("Familia", ["TODOS"] + familias, key="filtro_familia_hist_luc")
    with col2:
        equipo = st.selectbox("Equipo Lucarbal", ["TODOS"] + equipos, key="filtro_equipo_hist_luc")
    with col3:
        turno = st.selectbox("Turno", ["TODOS"] + turnos, key="filtro_turno_hist_luc")
    with col4:
        estado = st.selectbox("Estado", ["TODOS"] + estados, key="filtro_estado_hist_luc")
    with col5:
        rango = st.selectbox(
            "Periodo",
            ["Últimos 7 días", "Últimos 15 días", "Últimos 30 días", "Todo"],
            key="filtro_periodo_hist_luc",
        )

    df_filtrado = df.copy()

    if familia != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["familia"] == familia]
    if equipo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["equipo"] == equipo]
    if turno != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["turno"] == turno]
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

    total_eventos = int((df_filtrado["tipo_registro"] == "EVENTO EN EQUIPO").sum())
    total_taller = int((df_filtrado["tipo_registro"] == "TRABAJO DE TALLER").sum())

    mensaje = f"Registros encontrados: **{len(df_filtrado)}** · Eventos de equipo: **{total_eventos}**"
    if incluir_taller:
        mensaje += f" · Taller: **{total_taller}**"
    mensaje += " · ordenado del más reciente al más antiguo."
    st.info(mensaje)

    st.markdown("---")

    for _, row in df_filtrado.iterrows():
        mostrar_tarjeta(row)
