# ==========================================================
# REGISTRO_LUCARBAL.PY
# REGISTRO DE EVENTOS LUCARBAL
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

from database import (
    cargar_equipos_lucarbal,
    guardar_lucarbal_evento,
    generar_id_lucarbal
)

from config import (
    ESTADOS_LUCARBAL,
    TIPOS_MANTENIMIENTO
)


# ==========================================================
# FOTO BASE64 CON COMPRESIÓN INTELIGENTE
# ==========================================================

def convertir_foto_base64(archivo):

    if archivo is None:
        return "SIN FOTO"

    try:
        imagen_original = Image.open(archivo)
        imagen_original = imagen_original.convert("RGB")

        ancho_max = 650
        alto_max = 650
        calidad = 45

        while True:

            imagen = imagen_original.copy()
            imagen.thumbnail((ancho_max, alto_max))

            buffer = BytesIO()

            imagen.save(
                buffer,
                format="JPEG",
                quality=calidad,
                optimize=True
            )

            foto_base64 = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

            resultado = f"data:image/jpeg;base64,{foto_base64}"

            if len(resultado) < 35000:
                return resultado

            calidad -= 5
            ancho_max -= 70
            alto_max -= 70

            if calidad < 18:
                calidad = 18

            if ancho_max < 250:
                ancho_max = 250

            if alto_max < 250:
                alto_max = 250

            if calidad == 18 and ancho_max == 250:
                st.warning(
                    "⚠️ La foto fue comprimida automáticamente "
                    "para poder guardarse en Google Sheets."
                )
                return resultado

    except Exception as e:
        st.error(f"Error al procesar la foto: {e}")
        return "SIN FOTO"


# ==========================================================
# FORMATEAR HORA
# ==========================================================

def formatear_hora(texto_hora):

    texto_hora = str(texto_hora).strip()

    if texto_hora == "":
        return ""

    if ":" in texto_hora:
        return texto_hora

    solo_numeros = "".join(
        filter(str.isdigit, texto_hora)
    )

    if solo_numeros == "":
        return texto_hora

    solo_numeros = solo_numeros[-4:]

    if len(solo_numeros) == 1:
        solo_numeros = "000" + solo_numeros

    elif len(solo_numeros) == 2:
        solo_numeros = "00" + solo_numeros

    elif len(solo_numeros) == 3:
        solo_numeros = "0" + solo_numeros

    hora = solo_numeros[:2]
    minuto = solo_numeros[2:]

    return f"{hora}:{minuto}"


def convertir_hora(texto_hora):

    try:
        return datetime.strptime(
            texto_hora.strip(),
            "%H:%M"
        ).time()

    except Exception:
        return None


# ==========================================================
# REGISTRO LUCARBAL
# ==========================================================

def registro_lucarbal():

    st.title("🚛 Registro Evento - LUCARBAL")
    st.markdown("---")

    if "reset_lucarbal" not in st.session_state:
        st.session_state.reset_lucarbal = 0

    reset_id = st.session_state.reset_lucarbal

    df = cargar_equipos_lucarbal()

    if df.empty:
        st.error("No hay equipos cargados en la hoja equipos_lucarbal.")
        return

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    columnas_requeridas = [
        "familia_equipo",
        "codigo_lucarbal",
        "codigo_cognos",
        "marca"
    ]

    for col in columnas_requeridas:
        if col not in df.columns:
            st.error(
                f"Falta la columna '{col}' en la hoja equipos_lucarbal."
            )
            return

    for col in columnas_requeridas:
        df[col] = df[col].astype(str).str.strip()

    # ======================================================
    # DATOS GENERALES
    # ======================================================

    st.markdown("### 📅 Datos generales")

    col_fecha, col_turno = st.columns(2)

    with col_fecha:
        fecha = st.date_input(
            "Fecha reporte",
            value=datetime.today().date(),
            key=f"fecha_luc_{reset_id}"
        )

    with col_turno:
        turno = st.selectbox(
            "Turno",
            [
                "DIA",
                "NOCHE"
            ],
            key=f"turno_luc_{reset_id}"
        )

    tecnico = str(st.session_state.nombre).strip()
    dni = str(st.session_state.dni).strip()

    col_tec, col_dni = st.columns(2)

    with col_tec:
        st.text_input(
            "Técnico responsable",
            value=tecnico,
            disabled=True,
            key=f"tec_{reset_id}"
        )

    with col_dni:
        st.text_input(
            "DNI",
            value=dni,
            disabled=True,
            key=f"dni_luc_{reset_id}"
        )

    # ======================================================
    # EQUIPO
    # ======================================================

    st.markdown("### 🚛 Selección de equipo")

    familias = sorted(
        df["familia_equipo"]
        .dropna()
        .unique()
        .tolist()
    )

    familia = st.selectbox(
        "Familia equipo",
        familias,
        key=f"fam_{reset_id}"
    )

    df_filtrado = df[
        df["familia_equipo"] == familia
    ].copy()

    equipos = sorted(
        df_filtrado["codigo_lucarbal"]
        .dropna()
        .unique()
        .tolist()
    )

    codigo_lucarbal = st.selectbox(
        "Equipo",
        equipos,
        key=f"equipo_{reset_id}"
    )

    fila = df_filtrado[
        df_filtrado["codigo_lucarbal"] == codigo_lucarbal
    ].iloc[0]

    codigo_cognos = str(fila["codigo_cognos"]).strip()
    marca = str(fila["marca"]).strip()

    st.success(
        f"Equipo Cognos: {codigo_cognos}"
    )

    st.info(
        f"Marca: {marca}"
    )

    # ======================================================
    # MANTENIMIENTO
    # ======================================================

    tipo_mantenimiento = st.selectbox(
        "Tipo mantenimiento",
        TIPOS_MANTENIMIENTO,
        key=f"tipo_mant_{reset_id}"
    )

    # ======================================================
    # HORAS
    # ======================================================

    st.markdown("### ⏱ Registro tiempos")

    col3, col4 = st.columns(2)

    with col3:
        hora_falla_input = st.text_input(
            "Hora falla",
            placeholder="715 → 07:15",
            key=f"hf_{reset_id}"
        )

    with col4:
        hora_sub_input = st.text_input(
            "Hora subsanada",
            placeholder="1530 → 15:30",
            key=f"hs_{reset_id}"
        )

    hora_falla_txt = formatear_hora(
        hora_falla_input
    )

    hora_sub_txt = formatear_hora(
        hora_sub_input
    )

    if hora_falla_input:
        st.caption(
            f"Hora falla detectada: {hora_falla_txt}"
        )

    if hora_sub_input:
        st.caption(
            f"Hora subsanada detectada: {hora_sub_txt}"
        )

    hora_falla = convertir_hora(
        hora_falla_txt
    )

    hora_sub = convertir_hora(
        hora_sub_txt
    )

    tiempo_parada = None

    if hora_falla and hora_sub:

        inicio = datetime.combine(
            fecha,
            hora_falla
        )

        fin = datetime.combine(
            fecha,
            hora_sub
        )

        if fin < inicio:
            fin += timedelta(days=1)

        tiempo_parada = round(
            (fin - inicio).total_seconds() / 3600,
            2
        )

        st.info(
            f"Tiempo parada: {tiempo_parada} h"
        )

    elif hora_falla_input or hora_sub_input:
        st.warning(
            "Ingrese hora válida. Ejemplo: 715, 0715 o 07:15"
        )

    # ======================================================
    # DESCRIPCIÓN
    # ======================================================

    descripcion = st.text_area(
        "Descripción falla / trabajo realizado",
        height=150,
        key=f"desc_{reset_id}"
    )

    estado_operativo = st.selectbox(
        "Estado operativo",
        ESTADOS_LUCARBAL,
        key=f"estado_{reset_id}"
    )

    foto = st.file_uploader(
        "Subir evidencia",
        type=["jpg", "jpeg", "png"],
        key=f"foto_{reset_id}"
    )

    if foto is not None:
        st.image(
            foto,
            caption="Vista previa",
            use_container_width=True
        )

    # ======================================================
    # GUARDAR
    # ======================================================

    if st.button(
        "Guardar Evento Lucarbal",
        use_container_width=True,
        key=f"btn_guardar_lucarbal_{reset_id}"
    ):

        if hora_falla is None:
            st.error("Debes ingresar la hora de falla.")
            st.stop()

        if hora_sub is None:
            st.error("Debes ingresar la hora subsanada.")
            st.stop()

        if descripcion.strip() == "":
            st.error("Debe ingresar descripción.")
            st.stop()

        evento_id = generar_id_lucarbal()

        foto_base64 = convertir_foto_base64(
            foto
        )

        datos = [
            evento_id,
            str(fecha),
            turno,
            familia,
            codigo_lucarbal,
            codigo_cognos,
            marca,
            tipo_mantenimiento,
            hora_falla_txt,
            hora_sub_txt,
            tiempo_parada,
            descripcion,
            estado_operativo,
            tecnico,
            dni,
            foto_base64,
            str(datetime.now())
        ]

        guardar_lucarbal_evento(
            datos
        )

        st.success(
            "✅ Evento Lucarbal registrado correctamente."
        )

        st.session_state.reset_lucarbal += 1

        st.rerun()
