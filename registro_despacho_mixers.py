# ==========================================================
# REGISTRO_DESPACHO_MIXERS.PY
# REGISTRO DE DESPACHO DE MIXERS - PLANTA MÓVIL
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from zoneinfo import ZoneInfo

from database import (
    guardar_despacho_mixer,
    generar_id_despacho_mixer
)

from config import ESTADOS_DESPACHO_MIXERS


# ==========================================================
# FECHA / HORA PERÚ
# ==========================================================

def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


# ==========================================================
# MIXERS Y CÓDIGOS COGNOS
# ==========================================================

MIXERS_COGNOS = {
    "MIX-510": "SEP-MIX-0002",
    "MIX-508": "SEP-MIX-0003",
    "MIX-509": "SEP-MIX-0004",
    "MIX-511": "SEP-MIX-0005"
}


CAUSAS_ESPERA = [
    "SIN ESPERA",
    "ESPERA POR SERVICIOS MINA",
    "ESPERA POR PLANTA",
    "ESPERA POR MANTENIMIENTO",
    "ESPERA POR OPERADOR",
    "ESPERA POR MIXER",
    "ESPERA POR MATERIAL",
    "ESPERA POR COORDINACIÓN",
    "OTRO"
]


# ==========================================================
# FOTO BASE64 CON COMPRESIÓN INTELIGENTE
# ==========================================================

def convertir_foto_base64(archivo):

    if archivo is None:
        return "SIN FOTO"

    try:

        imagen_original = Image.open(archivo)
        imagen_original = imagen_original.convert("RGB")

        ancho_max = 700
        alto_max = 700
        calidad = 55

        while True:

            imagen = imagen_original.copy()

            imagen.thumbnail(
                (ancho_max, alto_max)
            )

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

            resultado = (
                f"data:image/jpeg;base64,"
                f"{foto_base64}"
            )

            if len(resultado) < 49000:
                return resultado

            calidad -= 5
            ancho_max -= 80
            alto_max -= 80

            if calidad < 20:
                calidad = 20

            if ancho_max < 300:
                ancho_max = 300

            if alto_max < 300:
                alto_max = 300

            if (
                calidad == 20
                and ancho_max == 300
            ):

                st.warning(
                    "⚠️ La foto fue comprimida automáticamente "
                    "para poder guardarse."
                )

                return resultado

    except Exception as e:
        return f"ERROR FOTO: {e}"


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


# ==========================================================
# VALIDAR HORA
# ==========================================================

def convertir_hora(texto_hora):

    try:
        return datetime.strptime(
            texto_hora.strip(),
            "%H:%M"
        ).time()

    except Exception:
        return None


# ==========================================================
# REGISTRO DESPACHO MIXERS
# ==========================================================

def registro_despacho_mixers():

    st.title("🚚 Registro de Despacho de Mixers")
    st.markdown("---")

    if "reset_form_despacho_mixers" not in st.session_state:
        st.session_state.reset_form_despacho_mixers = 0

    reset_id = st.session_state.reset_form_despacho_mixers

    # ======================================================
    # DATOS GENERALES
    # ======================================================

    st.markdown("### 📅 Datos generales")

    col_fecha, col_turno, col_supervisor = st.columns(3)

    with col_fecha:

        fecha = st.date_input(
            "Fecha",
            value=ahora_peru().date(),
            key=f"fecha_despacho_mixer_{reset_id}"
        )

    with col_turno:

        turno = st.selectbox(
            "Turno",
            [
                "DÍA",
                "NOCHE"
            ],
            key=f"turno_despacho_mixer_{reset_id}"
        )

    supervisor = str(
        st.session_state.nombre
    ).strip()

    with col_supervisor:

        st.text_input(
            "Supervisor",
            value=supervisor,
            disabled=True,
            key=f"supervisor_despacho_mixer_{reset_id}"
        )

    st.markdown("---")

    # ======================================================
    # IDENTIFICACIÓN MIXER
    # ======================================================

    st.markdown("### 🚛 Identificación del mixer")

    col_mixer, col_codigo = st.columns(2)

    with col_mixer:

        mixer = st.selectbox(
            "Mixer",
            list(MIXERS_COGNOS.keys()),
            key=f"mixer_despacho_{reset_id}"
        )

    codigo_cognos = MIXERS_COGNOS[mixer]

    with col_codigo:

        st.text_input(
            "Código COGNOS",
            value=codigo_cognos,
            disabled=True,
            key=f"codigo_cognos_despacho_{reset_id}"
        )

    # ======================================================
    # TIEMPOS
    # ======================================================

    st.markdown("---")
    st.markdown("### ⏱ Registro de tiempos")

    col_llegada, col_inicio, col_salida = st.columns(3)

    with col_llegada:

        hora_llegada_input = st.text_input(
            "Hora llegada",
            placeholder="Ejemplo: 715 → 07:15",
            key=f"hora_llegada_despacho_{reset_id}"
        )

    with col_inicio:

        hora_inicio_carga_input = st.text_input(
            "Hora inicio carga",
            placeholder="Ejemplo: 730 → 07:30",
            key=f"hora_inicio_carga_despacho_{reset_id}"
        )

    with col_salida:

        hora_salida_input = st.text_input(
            "Hora salida",
            placeholder="Ejemplo: 755 → 07:55",
            key=f"hora_salida_despacho_{reset_id}"
        )

    hora_llegada_txt = formatear_hora(
        hora_llegada_input
    )

    hora_inicio_carga_txt = formatear_hora(
        hora_inicio_carga_input
    )

    hora_salida_txt = formatear_hora(
        hora_salida_input
    )

    if hora_llegada_input:
        st.caption(
            f"Hora llegada detectada: {hora_llegada_txt}"
        )

    if hora_inicio_carga_input:
        st.caption(
            f"Hora inicio carga detectada: {hora_inicio_carga_txt}"
        )

    if hora_salida_input:
        st.caption(
            f"Hora salida detectada: {hora_salida_txt}"
        )

    hora_llegada = convertir_hora(
        hora_llegada_txt
    )

    hora_inicio_carga = convertir_hora(
        hora_inicio_carga_txt
    )

    hora_salida = convertir_hora(
        hora_salida_txt
    )

    tiempo_espera_min = None
    tiempo_total_min = None

    if (
        hora_llegada
        and hora_inicio_carga
        and hora_salida
    ):

        llegada_dt = datetime.combine(
            fecha,
            hora_llegada
        )

        inicio_carga_dt = datetime.combine(
            fecha,
            hora_inicio_carga
        )

        salida_dt = datetime.combine(
            fecha,
            hora_salida
        )

        if inicio_carga_dt < llegada_dt:
            inicio_carga_dt += timedelta(days=1)

        if salida_dt < llegada_dt:
            salida_dt += timedelta(days=1)

        if salida_dt < inicio_carga_dt:
            salida_dt += timedelta(days=1)

        tiempo_espera_min = round(
            (
                inicio_carga_dt - llegada_dt
            ).total_seconds() / 60,
            2
        )

        tiempo_total_min = round(
            (
                salida_dt - llegada_dt
            ).total_seconds() / 60,
            2
        )

        st.info(
            f"Tiempo de espera: {tiempo_espera_min} min | "
            f"Tiempo total: {tiempo_total_min} min"
        )

    elif (
        hora_llegada_input
        or hora_inicio_carga_input
        or hora_salida_input
    ):

        st.warning(
            "Ingrese horas válidas. Ejemplo: 715, 0715 o 07:15"
        )

    # ======================================================
    # DESPACHO / CAUSA / FOTO
    # ======================================================

    st.markdown("---")
    st.markdown("### 📦 Información del despacho")

    metros_cubicos = st.number_input(
        "Metros cúbicos despachados (m³)",
        min_value=0.0,
        step=0.5,
        format="%.2f",
        key=f"metros_cubicos_despacho_{reset_id}"
    )

    causa_espera = st.selectbox(
        "Causa de espera / demora",
        CAUSAS_ESPERA,
        key=f"causa_espera_despacho_{reset_id}"
    )

    detalle = st.text_area(
        "Detalle / observación",
        placeholder=(
            "Ejemplo: Mixer esperó por falta de solicitud de Servicios Mina, "
            "planta en espera, demora por coordinación, etc."
        ),
        height=120,
        key=f"detalle_despacho_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS_DESPACHO_MIXERS,
        key=f"estado_despacho_{reset_id}"
    )

    evidencia = st.file_uploader(
        "Subir evidencia fotográfica del mixer",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key=f"evidencia_despacho_{reset_id}"
    )

    if evidencia is not None:

        st.image(
            evidencia,
            caption="Vista previa de evidencia",
            use_container_width=True
        )

    # ======================================================
    # GUARDAR
    # ======================================================

    if st.button(
        "Guardar Despacho Mixer",
        use_container_width=True,
        key=f"btn_guardar_despacho_{reset_id}"
    ):

        if hora_llegada is None:
            st.error(
                "Debes ingresar una hora de llegada válida."
            )
            st.stop()

        if hora_inicio_carga is None:
            st.error(
                "Debes ingresar una hora de inicio de carga válida."
            )
            st.stop()

        if hora_salida is None:
            st.error(
                "Debes ingresar una hora de salida válida."
            )
            st.stop()

        if metros_cubicos <= 0:
            st.error(
                "Debes ingresar los metros cúbicos despachados."
            )
            st.stop()

        if (
            causa_espera != "SIN ESPERA"
            and detalle.strip() == ""
        ):
            st.error(
                "Si existe espera o demora, debes ingresar el detalle."
            )
            st.stop()

        evidencia_guardada = convertir_foto_base64(
            evidencia
        )

        id_despacho = generar_id_despacho_mixer()

        datos = [
            id_despacho,
            str(fecha),
            turno,
            supervisor,
            mixer,
            codigo_cognos,
            hora_llegada_txt,
            hora_inicio_carga_txt,
            hora_salida_txt,
            tiempo_espera_min,
            tiempo_total_min,
            metros_cubicos,
            causa_espera,
            detalle,
            estado,
            evidencia_guardada
        ]

        guardar_despacho_mixer(
            datos
        )

        st.success(
            "✅ Despacho de mixer registrado correctamente."
        )

        st.session_state.reset_form_despacho_mixers += 1
        st.rerun()