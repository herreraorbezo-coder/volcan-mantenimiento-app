# ==========================================================
# EDITAR_REGISTROS.PY
# EDICIÓN CONTROLADA DE EVENTOS DE BOMBEO Y LUCARBAL
# ==========================================================

import base64
import unicodedata
from datetime import datetime, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from PIL import Image

from config import ESTADOS, ESTADOS_LUCARBAL, TIPOS_MANTENIMIENTO
from database import (
    actualizar_bitacora,
    actualizar_lucarbal_evento,
    cargar_bitacora,
    cargar_lucarbal_eventos,
    refrescar_cache_datos,
)


def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


def _normalizar(texto):
    valor = unicodedata.normalize("NFKD", str(texto or ""))
    valor = "".join(c for c in valor if not unicodedata.combining(c))
    return " ".join(valor.lower().strip().replace("_", " ").split())


def _columna(df, *alternativas):
    mapa = {_normalizar(c): c for c in df.columns}
    for alternativa in alternativas:
        encontrada = mapa.get(_normalizar(alternativa))
        if encontrada:
            return encontrada
    return None


def _valor(fila, *alternativas, defecto=""):
    for alternativa in alternativas:
        for columna in fila.index:
            if _normalizar(columna) == _normalizar(alternativa):
                valor = fila.get(columna, defecto)
                if pd.isna(valor):
                    return defecto
                return str(valor)
    return defecto


def _foto_base64(archivo, limite=35000):
    if archivo is None:
        return None
    imagen_original = Image.open(archivo).convert("RGB")
    ancho = 650
    alto = 650
    calidad = 45

    while True:
        imagen = imagen_original.copy()
        imagen.thumbnail((ancho, alto))
        buffer = BytesIO()
        imagen.save(buffer, format="JPEG", quality=calidad, optimize=True)
        contenido = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
        if len(contenido) < limite:
            return contenido
        calidad = max(calidad - 5, 18)
        ancho = max(ancho - 70, 250)
        alto = max(alto - 70, 250)
        if calidad == 18 and ancho == 250:
            return contenido


def _hora_valida(texto):
    texto = str(texto).strip().replace(".", ":")
    if not texto:
        return None
    if ":" not in texto:
        texto = texto.zfill(4)
        texto = f"{texto[:-2]}:{texto[-2:]}"
    try:
        return datetime.strptime(texto, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


def _calcular_horas(hora_inicio, hora_fin):
    inicio = datetime.strptime(hora_inicio, "%H:%M")
    fin = datetime.strptime(hora_fin, "%H:%M")
    if fin < inicio:
        fin += timedelta(days=1)
    return round((fin - inicio).total_seconds() / 3600, 2)


def _puede_editar(fila, empresa_modulo):
    rol = str(st.session_state.get("rol", "")).upper().strip()
    empresa = str(st.session_state.get("empresa", "")).upper().strip()
    dni = str(st.session_state.get("dni", "")).strip()
    nombre = str(st.session_state.get("nombre", "")).strip().upper()

    if dni == "75394588" or rol in ["ADMIN", "GERENTE", "PLANNER"]:
        return True
    if empresa != empresa_modulo:
        return False

    dni_registro = _valor(fila, "dni").strip()
    tecnico_registro = _valor(fila, "tecnico", "técnico").strip().upper()
    return (dni_registro and dni_registro == dni) or (tecnico_registro and tecnico_registro == nombre)


def _preparar_dataframe(df):
    if df.empty:
        return df
    fecha_col = _columna(df, "fecha")
    if fecha_col:
        df = df.copy()
        df["__fecha"] = pd.to_datetime(df[fecha_col], errors="coerce")
        df = df.sort_values("__fecha", ascending=False, na_position="last")
    return df


def _selector_registro(df, prefijo, etiqueta_equipo):
    id_col = _columna(df, "id")
    if not id_col:
        st.error("La hoja no contiene la columna ID.")
        return None

    opciones = []
    indices = []
    for idx, fila in df.iterrows():
        if not _puede_editar(fila, "LUCARBAL" if prefijo == "luc" else "VOLCAN"):
            continue
        rid = _valor(fila, "id")
        equipo = _valor(fila, etiqueta_equipo, "codigo", "código")
        fecha = _valor(fila, "fecha")
        tecnico = _valor(fila, "tecnico", "técnico")
        opciones.append(f"{rid} | {fecha} | {equipo} | {tecnico}")
        indices.append(idx)

    if not opciones:
        st.info("No tienes registros disponibles para editar con tu usuario.")
        return None

    seleccion = st.selectbox("Selecciona el reporte", opciones, key=f"selector_{prefijo}")
    return df.loc[indices[opciones.index(seleccion)]]


def _editor_bombeo():
    df = _preparar_dataframe(cargar_bitacora())
    if df.empty:
        st.info("No existen eventos de bombeo registrados.")
        return

    fila = _selector_registro(df, "bom", "codigo")
    if fila is None:
        return

    rid = _valor(fila, "id")
    st.caption(f"Editando evento: {rid}. El ID y el técnico original no se modifican.")

    with st.form(f"form_editar_bombeo_{rid}"):
        c1, c2 = st.columns(2)
        hora_inicio = c1.text_input("Hora de falla", value=_valor(fila, "hora_falla"))
        hora_fin = c2.text_input("Hora subsanada", value=_valor(fila, "hora_subsanada"))

        tipo_actual = _valor(fila, "tipo_mantenimiento")
        opciones_tipo = list(TIPOS_MANTENIMIENTO)
        if tipo_actual and tipo_actual not in opciones_tipo:
            opciones_tipo.insert(0, tipo_actual)
        tipo = st.selectbox("Tipo de mantenimiento", opciones_tipo, index=max(opciones_tipo.index(tipo_actual), 0) if tipo_actual in opciones_tipo else 0)

        estado_actual = _valor(fila, "estado")
        opciones_estado = list(ESTADOS)
        if estado_actual and estado_actual not in opciones_estado:
            opciones_estado.insert(0, estado_actual)
        estado = st.selectbox("Estado", opciones_estado, index=opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0)

        tipo_falla = st.text_input("Falla / intervención", value=_valor(fila, "tipo_falla"))
        causa = st.text_area("Causa preliminar", value=_valor(fila, "causa_preliminar"))
        repuesto = st.text_area("Repuesto requerido / utilizado", value=_valor(fila, "repuesto_requerido", "repuesto"))
        descripcion = st.text_area("Descripción del trabajo", value=_valor(fila, "descripcion"), height=130)
        foto = st.file_uploader("Reemplazar o agregar fotografía", type=["jpg", "jpeg", "png"], key=f"foto_bom_{rid}")
        st.caption("Si no seleccionas una foto nueva, se conserva la fotografía actual.")
        guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

    if guardar:
        hi = _hora_valida(hora_inicio)
        hf = _hora_valida(hora_fin)
        if not hi or not hf:
            st.error("Las horas deben tener formato HH:MM, por ejemplo 07:15 o 23:40.")
            return
        if not descripcion.strip():
            st.error("La descripción no puede quedar vacía.")
            return

        cambios = {
            "hora_falla": hi,
            "hora_subsanada": hf,
            "tiempo_parada": _calcular_horas(hi, hf),
            "tipo_mantenimiento": tipo,
            "tipo_falla": tipo_falla.strip(),
            "causa_preliminar": causa.strip(),
            "repuesto_requerido": repuesto.strip(),
            "descripcion": descripcion.strip(),
            "estado": estado,
        }
        nueva_foto = _foto_base64(foto, limite=49000)
        if nueva_foto:
            cambios["foto"] = nueva_foto

        actualizar_bitacora(
            rid,
            cambios,
            modificado_por=f"{st.session_state.get('nombre', '')} - DNI {st.session_state.get('dni', '')}",
            fecha_modificacion=str(ahora_peru()),
        )
        st.success("✅ Evento de bombeo actualizado correctamente.")
        st.rerun()


def _editor_lucarbal():
    df = _preparar_dataframe(cargar_lucarbal_eventos())
    if df.empty:
        st.info("No existen eventos Lucarbal registrados.")
        return

    fila = _selector_registro(df, "luc", "codigo_lucarbal")
    if fila is None:
        return

    rid = _valor(fila, "id")
    st.caption(f"Editando evento: {rid}. El ID, equipo y técnico original no se modifican.")

    with st.form(f"form_editar_lucarbal_{rid}"):
        c1, c2 = st.columns(2)
        hora_inicio = c1.text_input("Hora inicio de parada", value=_valor(fila, "hora_falla"))
        hora_fin = c2.text_input("Hora subsanada", value=_valor(fila, "hora_subsanada"))

        tipo_actual = _valor(fila, "tipo_mantenimiento")
        opciones_tipo = list(TIPOS_MANTENIMIENTO)
        if tipo_actual and tipo_actual not in opciones_tipo:
            opciones_tipo.insert(0, tipo_actual)
        tipo = st.selectbox("Tipo de mantenimiento", opciones_tipo, index=opciones_tipo.index(tipo_actual) if tipo_actual in opciones_tipo else 0)

        estado_actual = _valor(fila, "estado_operativo")
        opciones_estado = list(ESTADOS_LUCARBAL)
        if estado_actual and estado_actual not in opciones_estado:
            opciones_estado.insert(0, estado_actual)
        estado = st.selectbox("Estado operativo", opciones_estado, index=opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0)

        descripcion = st.text_area("Descripción de falla / trabajo realizado", value=_valor(fila, "descripcion"), height=140)
        requiere_actual = _valor(fila, "requiere_repuesto").upper() or "NO"
        requiere = st.selectbox("¿Requiere repuesto?", ["NO", "SI"], index=1 if requiere_actual == "SI" else 0)
        detalle = st.text_area("Detalle del repuesto", value=_valor(fila, "detalle_repuesto"))
        foto = st.file_uploader("Reemplazar o agregar fotografía", type=["jpg", "jpeg", "png"], key=f"foto_luc_{rid}")
        st.caption("Si no seleccionas una foto nueva, se conserva la fotografía actual.")
        guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

    if guardar:
        hi = _hora_valida(hora_inicio)
        hf = _hora_valida(hora_fin)
        if not hi or not hf:
            st.error("Las horas deben tener formato HH:MM, por ejemplo 07:15 o 23:40.")
            return
        if not descripcion.strip():
            st.error("La descripción no puede quedar vacía.")
            return
        if requiere == "SI" and not detalle.strip():
            st.error("Debes ingresar el detalle del repuesto.")
            return

        cambios = {
            "hora_falla": hi,
            "hora_subsanada": hf,
            "tiempo_parada": _calcular_horas(hi, hf),
            "tipo_mantenimiento": tipo,
            "descripcion": descripcion.strip(),
            "estado_operativo": estado,
            "requiere_repuesto": requiere,
            "detalle_repuesto": detalle.strip() if requiere == "SI" else "",
        }
        nueva_foto = _foto_base64(foto)
        if nueva_foto:
            cambios["foto"] = nueva_foto

        actualizar_lucarbal_evento(
            rid,
            cambios,
            modificado_por=f"{st.session_state.get('nombre', '')} - DNI {st.session_state.get('dni', '')}",
            fecha_modificacion=str(ahora_peru()),
        )
        st.success("✅ Evento Lucarbal actualizado correctamente.")
        st.rerun()


def editar_registros():
    st.title("✏️ Editar reportes")
    st.caption("Corrige horas, descripción, estado, repuestos o agrega una fotografía sin crear un registro duplicado.")

    if st.button("🔄 Actualizar lista de reportes", use_container_width=True):
        refrescar_cache_datos()
        st.rerun()

    empresa = str(st.session_state.get("empresa", "")).upper().strip()
    rol = str(st.session_state.get("rol", "")).upper().strip()
    acceso_total = str(st.session_state.get("dni", "")) == "75394588" or rol in ["ADMIN", "GERENTE", "PLANNER"]

    if acceso_total:
        tab_bom, tab_luc = st.tabs(["⚙️ Eventos de bombeo", "🚛 Eventos Lucarbal"])
        with tab_bom:
            _editor_bombeo()
        with tab_luc:
            _editor_lucarbal()
    elif empresa == "VOLCAN":
        _editor_bombeo()
    elif empresa == "LUCARBAL":
        _editor_lucarbal()
    else:
        st.warning("La edición se encuentra habilitada actualmente para Bombeo VOLCAN y Eventos LUCARBAL.")