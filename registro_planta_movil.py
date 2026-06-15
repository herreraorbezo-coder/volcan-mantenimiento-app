# ==========================================================
# REGISTRO_PLANTA_MOVIL.PY
# REGISTRO DE MANTENIMIENTO - PLANTA MÓVIL
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from zoneinfo import ZoneInfo

from database import (
    guardar_planta_movil_evento,
    generar_id_planta_movil
)

from config import ESTADOS_PLANTA_MOVIL


# ==========================================================
# FECHA / HORA PERÚ
# ==========================================================

def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


# ==========================================================
# ÁREAS Y EQUIPOS - PLANTA MÓVIL
# ==========================================================

AREAS_PLANTA_MOVIL = {
    "Área 1 - Silo de Cemento": [
        "Sinfín",
        "Extractor de polvo",
        "Motor de accionamiento sinfín inferior",
        "Vibrador de silo",
        "Motor eléctrico - silo",
        "Reductor"
    ],
    "Área 2 - Tolva de Agregado": [
        "Reductor-mezclador",
        "Tolva de balanza de agregados",
        "Fajas de alimentación",
        "Tablero principal de operaciones",
        "Vibradores tolva agregado",
        "Motor bomba aditivo",
        "Motor bomba agua",
        "Motores mezclador",
        "Mariposas de descarga - balanza de cemento"
    ],
    "Área 3 - Faja Transportadora": [
        "Polines",
        "Chute de descarga",
        "Limpiador de faja",
        "Motor de descarga"
    ]
}


TIPOS_INTERVENCION = [
    "INS - Inspección",
    "M1 - Preventivo menor",
    "M2 - Preventivo intermedio",
    "M3 - Preventivo mayor",
    "MC - Correctivo",
    "CP - Correctivo programado"
]


ACTIVIDADES = [
    "Limpieza",
    "Engrase",
    "Inspección visual",
    "Ajuste",
    "Cambio componente",
    "Soldadura",
    "Lubricación",
    "Calibración",
    "Reparación",
    "Lavado",
    "Desatoro",
    "Cambio de aceite",
    "Cambio de rodamiento"
]


PUNTOS_LIMPIEZA = [
    "Zona inferior de tolva / descarga",
    "Tornillo sinfín y zona de alimentación",
    "Tolva de agregado / lavado interno",
    "Parte inferior de transportadores / zonas ocultas",
    "Chute de descarga / sistema vibratorio",
    "Plataforma superior / boca de acceso",
    "Faja transportadora"
]


PUNTOS_ENGRASE = [
    "Rodillo inferior / rodamiento tolva",
    "Motorreductor agitador izquierdo",
    "Motorreductor agitador derecho",
    "Poleas y rodillos faja transportadora",
    "Rodamientos internos del mezclador",
    "Acople / transmisión principal",
    "Sistema de transmisión inferior"
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
# REGISTRO PLANTA MÓVIL
# ==========================================================

def registro_planta_movil():

    st.title("🏗️ Registro de Mantenimiento - Planta Móvil")
    st.markdown("---")

    if "reset_form_planta_movil" not in st.session_state:
        st.session_state.reset_form_planta_movil = 0

    reset_id = st.session_state.reset_form_planta_movil

    # ======================================================
    # DATOS GENERALES
    # ======================================================

    st.markdown("### 📅 Datos generales")

    col_fecha, col_turno, col_tecnico = st.columns(3)

    with col_fecha:

        fecha_evento = st.date_input(
            "Fecha",
            value=ahora_peru().date(),
            key=f"fecha_planta_movil_{reset_id}"
        )

    with col_turno:

        turno = st.selectbox(
            "Turno",
            [
                "DÍA",
                "NOCHE"
            ],
            key=f"turno_planta_movil_{reset_id}"
        )

    tecnico = str(
        st.session_state.nombre
    ).strip()

    with col_tecnico:

        st.text_input(
            "Técnico",
            value=tecnico,
            disabled=True,
            key=f"tecnico_planta_movil_{reset_id}"
        )

    apoyo = st.text_input(
        "Apoyo / personal adicional",
        placeholder="Opcional: nombre de apoyo",
        key=f"apoyo_planta_movil_{reset_id}"
    )

    st.markdown("---")

    # ======================================================
    # ÁREA Y EQUIPO
    # ======================================================

    st.markdown("### 🏭 Área y equipo intervenido")

    col_area, col_equipo = st.columns(2)

    with col_area:

        area = st.selectbox(
            "Área",
            list(AREAS_PLANTA_MOVIL.keys()),
            key=f"area_planta_movil_{reset_id}"
        )

    with col_equipo:

        equipo_punto = st.selectbox(
            "Equipo / punto",
            AREAS_PLANTA_MOVIL[area],
            key=f"equipo_punto_planta_movil_{reset_id}"
        )

    tipo_intervencion = st.selectbox(
        "Tipo de intervención",
        TIPOS_INTERVENCION,
        key=f"tipo_intervencion_planta_movil_{reset_id}"
    )

    actividad = st.multiselect(
        "Actividad realizada",
        ACTIVIDADES,
        key=f"actividad_planta_movil_{reset_id}"
    )

    st.markdown("---")

    # ======================================================
    # PUNTOS INTERVENIDOS
    # ======================================================

    st.markdown("### 🧹 Puntos intervenidos")

    col_limpieza, col_engrase = st.columns(2)

    with col_limpieza:

        puntos_limpieza = st.multiselect(
            "Puntos de limpieza",
            PUNTOS_LIMPIEZA,
            key=f"puntos_limpieza_planta_movil_{reset_id}"
        )

    with col_engrase:

        puntos_engrase = st.multiselect(
            "Puntos de engrase",
            PUNTOS_ENGRASE,
            key=f"puntos_engrase_planta_movil_{reset_id}"
        )

    st.markdown("---")

    # ======================================================
    # TIEMPOS
    # ======================================================

    st.markdown("### ⏱ Registro de tiempos")

    col_inicio, col_fin = st.columns(2)

    with col_inicio:

        hora_inicio_input = st.text_input(
            "Hora inicio",
            placeholder="Ejemplo: 715 → 07:15",
            key=f"hora_inicio_planta_movil_{reset_id}"
        )

    with col_fin:

        hora_fin_input = st.text_input(
            "Hora fin",
            placeholder="Ejemplo: 1530 → 15:30",
            key=f"hora_fin_planta_movil_{reset_id}"
        )

    hora_inicio_txt = formatear_hora(
        hora_inicio_input
    )

    hora_fin_txt = formatear_hora(
        hora_fin_input
    )

    if hora_inicio_input:
        st.caption(
            f"Hora inicio detectada: {hora_inicio_txt}"
        )

    if hora_fin_input:
        st.caption(
            f"Hora fin detectada: {hora_fin_txt}"
        )

    hora_inicio = convertir_hora(
        hora_inicio_txt
    )

    hora_fin = convertir_hora(
        hora_fin_txt
    )

    tiempo_parada_min = None

    if hora_inicio and hora_fin:

        inicio = datetime.combine(
            fecha_evento,
            hora_inicio
        )

        fin = datetime.combine(
            fecha_evento,
            hora_fin
        )

        if fin < inicio:
            fin += timedelta(days=1)

        tiempo_parada_min = round(
            (
                fin - inicio
            ).total_seconds() / 60,
            2
        )

        st.info(
            f"Tiempo registrado: {tiempo_parada_min} minutos"
        )

    elif hora_inicio_input or hora_fin_input:

        st.warning(
            "Ingrese hora válida. Ejemplo: 715, 0715 o 07:15"
        )

    # ======================================================
    # DETALLE / ESTADO / FOTO
    # ======================================================

    detalle = st.text_area(
        "Detalle del trabajo realizado / condición encontrada",
        height=120,
        key=f"detalle_planta_movil_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS_PLANTA_MOVIL,
        key=f"estado_planta_movil_{reset_id}"
    )

    evidencia = st.file_uploader(
        "Subir evidencia fotográfica",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key=f"evidencia_planta_movil_{reset_id}"
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
        "Guardar Registro Planta Móvil",
        use_container_width=True,
        key=f"btn_guardar_planta_movil_{reset_id}"
    ):

        if not actividad:
            st.error(
                "Debes seleccionar al menos una actividad realizada."
            )
            st.stop()

        if hora_inicio is None:
            st.error(
                "Debes ingresar una hora de inicio válida."
            )
            st.stop()

        if hora_fin is None:
            st.error(
                "Debes ingresar una hora fin válida."
            )
            st.stop()

        if detalle.strip() == "":
            st.error(
                "Debes ingresar el detalle del trabajo realizado."
            )
            st.stop()

        foto_guardada = convertir_foto_base64(
            evidencia
        )

        id_evento = generar_id_planta_movil()

        datos = [
            str(fecha_evento),
            turno,
            area,
            equipo_punto,
            tipo_intervencion,
            " | ".join(actividad),
            " | ".join(puntos_limpieza),
            " | ".join(puntos_engrase),
            hora_inicio_txt,
            hora_fin_txt,
            tiempo_parada_min,
            tecnico,
            apoyo,
            detalle,
            estado,
            foto_guardada,
            id_evento
        ]

        guardar_planta_movil_evento(
            datos
        )

        st.success(
            "✅ Registro de Planta Móvil guardado correctamente."
        )

        st.session_state.reset_form_planta_movil += 1
        st.rerun()