# ==========================================================
# REGISTRO_TRACKLESS.PY
# REGISTRO DE EVENTOS TRACKLESS
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

from database import (
    guardar_trackless,
    generar_id_trackless
)

from config import ESTADOS


EQUIPOS_TRACKLESS = {
    "JUMBO FRONTONERO": ["JUMBO-007", "JUMBO-008"],
    "EMPERNADOR": ["BOL-212", "BOL-213"],
    "TALADRO LARGO": ["JTL-001", "JTL-002"],
    "SCOOP": ["SCO-313", "SCO-314", "SCO-315", "SCO-316", "SCO-317", "SCO-322"],
    "MIXER": ["MIX-510", "MIX-508", "MIX-509", "MIX-511"],
    "LANZADOR": ["ROB-A16", "ROB-A17"],
    "DESATADOR": ["SCA-109", "SCA-110", "SCA-115"],
    "UTILITARIO": ["MTM-114", "MTM-115", "MTM-116"],
    "PLANTA": ["PLANTA FIJA", "PLANTA MÓVIL"],
    "OTROS": [
        "CISTERNA DE COMBUSTIBLE",
        "INYECTORA DE CEMENTO",
        "CAMION DE MATERIALES"
    ]
}


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

            if calidad == 20 and ancho_max == 300:
                st.warning("⚠️ La foto fue comprimida automáticamente para poder guardarse.")
                return resultado

    except Exception as e:
        return f"ERROR FOTO: {e}"


def formatear_hora(texto_hora):

    texto_hora = str(texto_hora).strip()

    if texto_hora == "":
        return ""

    if ":" in texto_hora:
        return texto_hora

    solo_numeros = "".join(filter(str.isdigit, texto_hora))

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


def clasificar_tipo_parada(tipo_parada):

    reglas = {
        "PARADA CORRECTIVO NO PROGRAMADO": {
            "afecta_global": "SI",
            "afecta_contratista": "SI",
            "afecta_mtbf": "SI",
            "afecta_mttr": "SI"
        },
        "PARADA MANTENIMIENTO PREVENTIVO": {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "SI"
        },
        "PARADA DE SEGURIDAD": {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "NO"
        },
        "PARADA DAÑO OPERATIVO": {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "NO"
        },
        "PARADA CONDICIÓN DE MINA": {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "NO"
        },
        "PARADA CORRECTIVO PROGRAMADO": {
            "afecta_global": "SI",
            "afecta_contratista": "SI",
            "afecta_mtbf": "NO",
            "afecta_mttr": "SI"
        },
        "PARADA POR IMPLEMENTACIÓN EQUIPO": {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "NO"
        }
    }

    return reglas.get(
        tipo_parada,
        {
            "afecta_global": "SI",
            "afecta_contratista": "NO",
            "afecta_mtbf": "NO",
            "afecta_mttr": "NO"
        }
    )


def registro_trackless():

    st.title("🚜 Registro de Evento - Flota Trackless")
    st.caption("Control de paradas · Disponibilidad global · Disponibilidad atribuible")
    st.markdown("---")

    if "reset_form_trackless" not in st.session_state:
        st.session_state.reset_form_trackless = 0

    reset_id = st.session_state.reset_form_trackless

    col0, col1 = st.columns(2)

    with col0:
        fecha = st.date_input(
            "Fecha del evento",
            value=datetime.today().date(),
            key=f"fecha_trackless_{reset_id}"
        )

    with col1:
        turno = st.selectbox(
            "Turno",
            ["DÍA", "NOCHE"],
            key=f"turno_trackless_{reset_id}"
        )

    st.markdown("### 🚜 Equipo")

    col2, col3 = st.columns(2)

    with col2:
        familia_equipo = st.selectbox(
            "Familia de equipo",
            list(EQUIPOS_TRACKLESS.keys()),
            key=f"familia_trackless_{reset_id}"
        )

    with col3:
        codigo_equipo = st.selectbox(
            "Código de equipo",
            EQUIPOS_TRACKLESS[familia_equipo],
            key=f"codigo_trackless_{reset_id}"
        )

    st.success(f"Equipo seleccionado: {familia_equipo} - {codigo_equipo}")

    st.markdown("### ⏱ Registro de tiempos")

    col4, col5 = st.columns(2)

    with col4:
        hora_parada_input = st.text_input(
            "Hora de parada",
            placeholder="Ejemplo: 715 → 07:15",
            key=f"hora_parada_trackless_{reset_id}"
        )

    with col5:
        hora_reinicio_input = st.text_input(
            "Hora finalizada / reinicio",
            placeholder="Ejemplo: 1530 → 15:30",
            key=f"hora_reinicio_trackless_{reset_id}"
        )

    hora_parada_txt = formatear_hora(hora_parada_input)
    hora_reinicio_txt = formatear_hora(hora_reinicio_input)

    if hora_parada_input:
        st.caption(f"Hora parada detectada: {hora_parada_txt}")

    if hora_reinicio_input:
        st.caption(f"Hora reinicio detectada: {hora_reinicio_txt}")

    hora_parada = convertir_hora(hora_parada_txt)
    hora_reinicio = convertir_hora(hora_reinicio_txt)

    tiempo_parada = None

    if hora_parada and hora_reinicio:

        inicio = datetime.combine(
            fecha,
            hora_parada
        )

        fin = datetime.combine(
            fecha,
            hora_reinicio
        )

        if fin < inicio:
            fin = fin + timedelta(days=1)

        tiempo_parada = round(
            (fin - inicio).total_seconds() / 3600,
            2
        )

        st.info(f"Tiempo de parada: {tiempo_parada} horas")

    elif hora_parada_input or hora_reinicio_input:
        st.warning("Ingrese hora válida. Ejemplo: 715, 0715 o 07:15")

    st.markdown("### 🧾 Clasificación de parada")

    tipo_parada = st.selectbox(
        "Tipo de parada",
        [
            "PARADA CORRECTIVO NO PROGRAMADO",
            "PARADA MANTENIMIENTO PREVENTIVO",
            "PARADA DE SEGURIDAD",
            "PARADA DAÑO OPERATIVO",
            "PARADA CONDICIÓN DE MINA",
            "PARADA CORRECTIVO PROGRAMADO",
            "PARADA POR IMPLEMENTACIÓN EQUIPO"
        ],
        key=f"tipo_parada_trackless_{reset_id}"
    )

    clasificacion = clasificar_tipo_parada(tipo_parada)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Afecta global", clasificacion["afecta_global"])
    c2.metric("Afecta contratista", clasificacion["afecta_contratista"])
    c3.metric("Afecta MTBF", clasificacion["afecta_mtbf"])
    c4.metric("Afecta MTTR", clasificacion["afecta_mttr"])

    descripcion = st.text_area(
        "Descripción / sustento del evento",
        placeholder="Detalle lo ocurrido en campo: falla, condición mina, operación, seguridad, etc.",
        height=130,
        key=f"descripcion_trackless_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS,
        key=f"estado_trackless_{reset_id}"
    )

    foto = st.file_uploader(
        "Subir evidencia fotográfica",
        type=["jpg", "jpeg", "png"],
        key=f"foto_trackless_{reset_id}"
    )

    if foto is not None:
        st.image(
            foto,
            caption="Vista previa de evidencia",
            use_container_width=True
        )

    if st.button(
        "Guardar Evento Trackless",
        use_container_width=True,
        key=f"btn_guardar_trackless_{reset_id}"
    ):

        if hora_parada is None:
            st.error("Debes ingresar la hora de parada. Ejemplo: 715 o 07:15.")
            st.stop()

        if hora_reinicio is None:
            st.error("Debes ingresar la hora finalizada / reinicio. Ejemplo: 1530 o 15:30.")
            st.stop()

        if descripcion.strip() == "":
            st.error("Debes ingresar una descripción del evento.")
            st.stop()

        evento_id = generar_id_trackless()

        foto_guardada = convertir_foto_base64(foto)

        datos = [
            evento_id,
            str(fecha),
            st.session_state.nombre,
            turno,
            familia_equipo,
            codigo_equipo,
            hora_parada_txt,
            hora_reinicio_txt,
            tiempo_parada,
            tipo_parada,
            clasificacion["afecta_global"],
            clasificacion["afecta_contratista"],
            clasificacion["afecta_mtbf"],
            clasificacion["afecta_mttr"],
            descripcion,
            estado,
            foto_guardada
        ]

        guardar_trackless(datos)

        st.success("✅ Evento Trackless registrado correctamente.")

        st.session_state.reset_form_trackless += 1

        st.rerun()
