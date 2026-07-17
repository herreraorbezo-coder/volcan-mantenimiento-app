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


def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


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
        "Filtro de la bomba de aditivo",
        "Motor Bomba de Engrase",
        "Motor de compresor",
        "Filtro Regulador",
        "Lubricador de Aire",
        "Mariposas de descarga - balanza de cemento"
    ],
    "Área 3 - Faja Transportadora": [
        "Polines",
        "Chute de descarga",
        "Limpiador de faja",
        "Motor de descarga",
        "Pull Cord"
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


MOTIVOS_PARADA = [
    "Mantenimiento programado",
    "Falla mecánica",
    "Falla eléctrica",
    "Falta de material",
    "Espera operación",
    "Otro"
]


def convertir_foto_base64(archivo):

    if archivo is None:
        return "SIN FOTO"

    try:
        imagen_original = Image.open(archivo).convert("RGB")

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
                st.warning(
                    "⚠️ La foto fue comprimida automáticamente."
                )
                return resultado

    except Exception as e:
        return f"ERROR FOTO: {e}"


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

    return f"{solo_numeros[:2]}:{solo_numeros[2:]}"


def convertir_hora(texto_hora):

    try:
        return datetime.strptime(
            texto_hora.strip(),
            "%H:%M"
        ).time()

    except Exception:
        return None


def calcular_tiempo_min(fecha, hora_inicio, hora_fin):

    inicio = datetime.combine(fecha, hora_inicio)
    fin = datetime.combine(fecha, hora_fin)

    if fin < inicio:
        fin += timedelta(days=1)

    return round(
        (fin - inicio).total_seconds() / 60,
        2
    )


def registro_planta_movil():

    st.title("🏗️ Registro de Mantenimiento - Planta Móvil")
    st.caption(
        "LIVERH · Intervención puntual, limpieza general, engrase general y parada general"
    )
    st.markdown("---")

    if "reset_form_planta_movil" not in st.session_state:
        st.session_state.reset_form_planta_movil = 0

    reset_id = st.session_state.reset_form_planta_movil

    st.markdown("### 📌 Tipo de registro")

    tipo_registro = st.radio(
        "Selecciona el tipo de registro",
        [
            "🔧 Intervención puntual",
            "🧹 Limpieza general",
            "🛢️ Engrase general",
            "⛔ Parada general"
        ],
        horizontal=True,
        key=f"tipo_registro_planta_{reset_id}"
    )

    st.markdown("---")
    st.markdown("### 📅 Datos generales")

    col_fecha, col_turno, col_tecnico = st.columns(3)

    with col_fecha:
        fecha = st.date_input(
            "Fecha",
            value=ahora_peru().date(),
            key=f"fecha_planta_{reset_id}"
        )

    with col_turno:
        turno = st.selectbox(
            "Turno",
            ["DÍA", "NOCHE"],
            key=f"turno_planta_{reset_id}"
        )

    tecnico = str(st.session_state.nombre).strip()

    with col_tecnico:
        st.text_input(
            "Técnico",
            value=tecnico,
            disabled=True,
            key=f"tecnico_planta_{reset_id}"
        )

    apoyo = st.text_input(
        "Apoyo / personal adicional",
        placeholder="Opcional",
        key=f"apoyo_planta_{reset_id}"
    )

    area = ""
    equipo_punto = ""
    tipo_intervencion = ""
    motivo_parada = ""
    tipo_lubricante = ""

    st.markdown("---")

    if tipo_registro == "🔧 Intervención puntual":

        st.markdown("### 🏭 Área y equipo intervenido")

        col_area, col_equipo = st.columns(2)

        with col_area:
            area = st.selectbox(
                "Área",
                list(AREAS_PLANTA_MOVIL.keys()),
                key=f"area_planta_{reset_id}"
            )

        with col_equipo:
            equipo_punto = st.selectbox(
                "Equipo / punto",
                AREAS_PLANTA_MOVIL[area],
                key=f"equipo_planta_{reset_id}"
            )

        tipo_intervencion = st.selectbox(
            "Tipo de intervención",
            TIPOS_INTERVENCION,
            key=f"tipo_intervencion_planta_{reset_id}"
        )

    elif tipo_registro == "🧹 Limpieza general":

        st.markdown("### 🧹 Limpieza general de fin de guardia")

        area = "Área 1 + Área 2 + Área 3"
        equipo_punto = "Planta móvil completa"
        tipo_intervencion = "M1 - Limpieza general"

        st.info(
            "Este registro aplica a limpieza general de planta móvil: "
            "silo, tolva de agregado y faja transportadora."
        )

    elif tipo_registro == "🛢️ Engrase general":

        st.markdown("### 🛢️ Engrase general")

        area = "Área 1 + Área 2 + Área 3"
        equipo_punto = "Puntos de engrase planta móvil"
        tipo_intervencion = "M1 - Engrase general"

        tipo_lubricante = st.selectbox(
            "Tipo de lubricante",
            ["GRASA", "ACEITE", "MIXTO"],
            key=f"lubricante_planta_{reset_id}"
        )

        st.info(
            "Este registro aplica al engrase general diario de puntos críticos "
            "de la planta móvil."
        )

    elif tipo_registro == "⛔ Parada general":

        st.markdown("### ⛔ Parada general de planta")

        area = "Área 1 + Área 2 + Área 3"
        equipo_punto = "Planta móvil completa"

        motivo_parada = st.selectbox(
            "Motivo de parada",
            MOTIVOS_PARADA,
            key=f"motivo_parada_planta_{reset_id}"
        )

        tipo_intervencion = "Parada general"

    st.markdown("---")
    st.markdown("### ⏱ Registro de tiempos")

    col_inicio, col_fin = st.columns(2)

    with col_inicio:
        hora_inicio_input = st.text_input(
            "Hora inicio",
            placeholder="Ejemplo: 715 → 07:15",
            key=f"hora_inicio_planta_{reset_id}"
        )

    with col_fin:
        hora_fin_input = st.text_input(
            "Hora fin",
            placeholder="Ejemplo: 1530 → 15:30",
            key=f"hora_fin_planta_{reset_id}"
        )

    hora_inicio_txt = formatear_hora(hora_inicio_input)
    hora_fin_txt = formatear_hora(hora_fin_input)

    if hora_inicio_input:
        st.caption(
            f"Hora inicio detectada: {hora_inicio_txt}"
        )

    if hora_fin_input:
        st.caption(
            f"Hora fin detectada: {hora_fin_txt}"
        )

    hora_inicio = convertir_hora(hora_inicio_txt)
    hora_fin = convertir_hora(hora_fin_txt)

    tiempo_parada_min = None

    if hora_inicio and hora_fin:

        tiempo_parada_min = calcular_tiempo_min(
            fecha,
            hora_inicio,
            hora_fin
        )

        st.info(
            f"Tiempo registrado: {tiempo_parada_min} minutos"
        )

    elif hora_inicio_input or hora_fin_input:

        st.warning(
            "Ingrese hora válida. Ejemplo: 715, 0715 o 07:15"
        )

    # ======================================================
    # REQUERIMIENTO DE REPUESTO / MATERIAL
    # ======================================================

    st.markdown("---")
    st.markdown("### 📦 Repuesto / material requerido")

    requiere_repuesto = st.checkbox(
        "¿Requiere repuesto o material para seguimiento?",
        key=f"requiere_repuesto_planta_{reset_id}"
    )

    repuesto_requerido = ""

    if requiere_repuesto:

        repuesto_requerido = st.text_input(
            "Indicar repuesto o material requerido",
            placeholder=(
                "Ejemplo: grasa EP2, rodamiento, polín, faja, sensor, "
                "aceite reductor, pernos, chumacera..."
            ),
            key=f"repuesto_requerido_planta_{reset_id}"
        )

    # ======================================================
    # DETALLE
    # ======================================================

    detalle_default = ""

    if tipo_registro == "🧹 Limpieza general":
        detalle_default = (
            "Limpieza general de fin de guardia en planta móvil. "
            "Retiro de material acumulado en silo, tolva, chute, zona de mezcla "
            "y faja transportadora."
        )

    elif tipo_registro == "🛢️ Engrase general":
        detalle_default = (
            "Engrase general diario de puntos críticos de planta móvil. "
            "Verificación de puntos móviles, rodamientos, polines, transmisión "
            "y componentes expuestos a polvo."
        )

    elif tipo_registro == "⛔ Parada general":
        detalle_default = (
            "Parada general de planta móvil. Se registra condición, motivo, "
            "tiempo de parada y acciones realizadas."
        )

    detalle = st.text_area(
        "Detalle técnico",
        value=detalle_default,
        height=130,
        key=f"detalle_planta_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS_PLANTA_MOVIL,
        key=f"estado_planta_{reset_id}"
    )

    evidencia = st.file_uploader(
        "Subir evidencia fotográfica",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key=f"evidencia_planta_{reset_id}"
    )

    if evidencia is not None:
        st.image(
            evidencia,
            caption="Vista previa de evidencia",
            use_container_width=True
        )

    if st.button(
        "Guardar Registro Planta Móvil",
        use_container_width=True,
        key=f"btn_guardar_planta_{reset_id}"
    ):

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

        if (
            requiere_repuesto
            and repuesto_requerido.strip() == ""
        ):
            st.error(
                "Marcaste que requiere repuesto/material, debes indicar cuál."
            )
            st.stop()

        if detalle.strip() == "":
            st.error(
                "Debes ingresar el detalle técnico."
            )
            st.stop()

        foto_guardada = convertir_foto_base64(
            evidencia
        )

        id_evento = generar_id_planta_movil()

        datos = [
            str(fecha),
            turno,
            tipo_registro,
            area,
            equipo_punto,
            tipo_intervencion,
            motivo_parada,
            tipo_lubricante,
            hora_inicio_txt,
            hora_fin_txt,
            tiempo_parada_min,
            tecnico,
            apoyo,
            "SI" if requiere_repuesto else "NO",
            repuesto_requerido,
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
