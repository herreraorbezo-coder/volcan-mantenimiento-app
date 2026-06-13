# ==========================================================
# REGISTRO_OT.PY
# REGISTRO DE EVENTO / FALLA DE BOMBA
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from zoneinfo import ZoneInfo
def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))

from database import (
    cargar_equipos,
    guardar_bitacora,
    generar_id
)

from config import ESTADOS


# ==========================================================
# TÉCNICOS MANTENIMIENTO MECÁNICO
# ==========================================================

TECNICOS_MANTTO = [
    "Raul Rosales",
    "Rolando Laurente",
    "Fernando Medina"
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

            # LÍMITE GOOGLE SHEETS
            if len(resultado) < 49000:
                return resultado

            # REDUCCIÓN PROGRESIVA
            calidad -= 5
            ancho_max -= 80
            alto_max -= 80

            if calidad < 20:
                calidad = 20

            if ancho_max < 300:
                ancho_max = 300

            if alto_max < 300:
                alto_max = 300

            # ÚLTIMO INTENTO
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
# OBTENER LISTA DE APOYOS DISPONIBLES
# ==========================================================

def obtener_apoyos_disponibles(tecnico_principal):

    tecnico_principal = str(tecnico_principal).strip().upper()

    apoyos = [
        tecnico
        for tecnico in TECNICOS_MANTTO
        if tecnico.upper().strip() != tecnico_principal
    ]

    return apoyos


# ==========================================================
# REGISTRO OT
# ==========================================================

def registro_ot():

    st.title("⚙️ Registro de Evento - Sistema Bombeo")
    st.markdown("---")

    if "reset_form_evento" not in st.session_state:
        st.session_state.reset_form_evento = 0

    reset_id = st.session_state.reset_form_evento

    df_equipos = cargar_equipos()

    df_equipos.columns = (
        df_equipos.columns
        .str.strip()
        .str.lower()
    )

    # ======================================================
    # FECHA Y TÉCNICO
    # ======================================================

    st.markdown("### 📅 Datos generales")

    col_fecha, col_tecnico = st.columns(2)

    with col_fecha:

        fecha_evento = st.date_input(
            "Fecha del evento",
            value=ahora_peru().date(),
            key=f"fecha_evento_bombeo_{reset_id}"
        )

    tecnico_principal = str(st.session_state.nombre).strip()

    with col_tecnico:

        st.text_input(
            "Técnico principal",
            value=tecnico_principal,
            disabled=True,
            key=f"tecnico_principal_bombeo_{reset_id}"
        )

    # ======================================================
    # APOYO DE TÉCNICOS
    # ======================================================

    apoyo_1 = ""
    apoyo_2 = ""

    tuvo_apoyo = st.checkbox(
        "¿Tuvo apoyo de otro técnico?",
        key=f"tuvo_apoyo_bombeo_{reset_id}"
    )

    if tuvo_apoyo:

        apoyos_disponibles = obtener_apoyos_disponibles(
            tecnico_principal
        )

        col_apoyo1, col_apoyo2 = st.columns(2)

        with col_apoyo1:

            apoyo_1 = st.selectbox(
                "Apoyo 1",
                [""] + apoyos_disponibles,
                key=f"apoyo_1_bombeo_{reset_id}"
            )

        apoyos_para_apoyo2 = [
            tecnico
            for tecnico in apoyos_disponibles
            if tecnico != apoyo_1
        ]

        with col_apoyo2:

            apoyo_2 = st.selectbox(
                "Apoyo 2",
                [""] + apoyos_para_apoyo2,
                key=f"apoyo_2_bombeo_{reset_id}"
            )

    st.markdown("---")

    # ======================================================
    # SISTEMA Y EQUIPO
    # ======================================================

    sistema = st.selectbox(
        "Sistema",
        ["BOMBEO"],
        key=f"sistema_bombeo_{reset_id}"
    )

    tipo_mantenimiento = st.selectbox(
        "Tipo de mantenimiento",
        [
            "PREVENTIVO",
            "CORRECTIVO"
        ],
        key=f"tipo_mantenimiento_bombeo_{reset_id}"
    )

    niveles = sorted(
        df_equipos["nivel"]
        .dropna()
        .unique()
        .tolist()
    )

    nivel = st.selectbox(
        "Nivel",
        niveles,
        key=f"nivel_bombeo_{reset_id}"
    )

    ubicaciones = (
        df_equipos[
            df_equipos["nivel"] == nivel
        ]["ubicacion"]
        .dropna()
        .unique()
        .tolist()
    )

    ubicacion = st.selectbox(
        "Ubicación",
        ubicaciones,
        key=f"ubicacion_bombeo_{reset_id}"
    )

    codigo = df_equipos[
        (df_equipos["nivel"] == nivel) &
        (df_equipos["ubicacion"] == ubicacion)
    ]["codigo"].values[0]

    st.success(
        f"Equipo identificado: {codigo}"
    )

    st.markdown(
        "### ⏱ Registro de tiempos"
    )

    col1, col2 = st.columns(2)

    with col1:

        hora_falla_input = st.text_input(
            "Hora falla",
            placeholder="Ejemplo: 715 → 07:15",
            key=f"hora_falla_txt_{reset_id}"
        )

    with col2:

        hora_subsanada_input = st.text_input(
            "Hora subsanada",
            placeholder="Ejemplo: 1530 → 15:30",
            key=f"hora_subsanada_txt_{reset_id}"
        )

    hora_falla_txt = formatear_hora(
        hora_falla_input
    )

    hora_subsanada_txt = formatear_hora(
        hora_subsanada_input
    )

    if hora_falla_input:
        st.caption(
            f"Hora falla detectada: "
            f"{hora_falla_txt}"
        )

    if hora_subsanada_input:
        st.caption(
            f"Hora subsanada detectada: "
            f"{hora_subsanada_txt}"
        )

    hora_falla = convertir_hora(
        hora_falla_txt
    )

    hora_subsanada = convertir_hora(
        hora_subsanada_txt
    )

    tiempo_parada = None

    if hora_falla and hora_subsanada:

        inicio = datetime.combine(
            fecha_evento,
            hora_falla
        )

        fin = datetime.combine(
            fecha_evento,
            hora_subsanada
        )

        if fin < inicio:
            fin += timedelta(days=1)

        tiempo_parada = round(
            (
                fin - inicio
            ).total_seconds() / 3600,
            2
        )

        st.info(
            f"Tiempo parada: "
            f"{tiempo_parada} horas"
        )

    elif hora_falla_input or hora_subsanada_input:
        st.warning(
            "Ingrese hora válida. "
            "Ejemplo: 715, 0715 o 07:15"
        )

    tipo_falla = st.selectbox(
        "¿Qué le pasó a la bomba?",
        [
            "INSPECCIÓN",
            "LUBRICACIÓN / ENGRASE",
            "LIMPIEZA",
            "MANTENIMIENTO PREVENTIVO",
            "FUGA",
            "RODAMIENTO",
            "SELLO MECÁNICO",
            "SOBRECALENTAMIENTO",
            "ATORO EN TUBERÍA",
            "OSCILACIÓN DE FAJA",
            "PÉRDIDA DE VISCOCIDAD DE ACEITE",
            "CAMBIO DE BOMBA",
            "CAMBIO DE MOTOR",
            "CAMBIO DE VÁLVULA CHECK",
            "CAMBIO DE JUNTA DE EXPANSIÓN"
        ],
        key=f"tipo_falla_bombeo_{reset_id}"
    )

    causa_preliminar = st.selectbox(
        "Causa preliminar",
        [
            "RUTINA PROGRAMADA",
            "CONDICIÓN NORMAL",
            "DESGASTE",
            "FALTA DE LUBRICACIÓN",
            "OPERACIÓN",
            "ALTA VIBRACIÓN",
            "CONTAMINACIÓN",
            "REQUIERE REPUESTO",
            "BAJA EFIENCIA DE CAUDAL"
        ],
        key=f"causa_preliminar_bombeo_{reset_id}"
    )

    # ======================================================
    # REPUESTO REQUERIDO
    # ======================================================

    repuesto_requerido = ""

    if causa_preliminar == "REQUIERE REPUESTO":

        repuesto_requerido = st.text_input(
            "Nombre del repuesto requerido",
            placeholder="Ejemplo: rodamiento, sello mecánico, válvula check...",
            key=f"repuesto_requerido_{reset_id}"
        )

    descripcion = st.text_area(
        "Descripción de la falla / trabajo realizado",
        height=120,
        key=f"descripcion_falla_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS,
        key=f"estado_bombeo_{reset_id}"
    )

    foto = st.file_uploader(
        "Subir evidencia fotográfica",
        type=["jpg", "jpeg", "png"],
        key=f"foto_bombeo_{reset_id}"
    )

    if foto is not None:

        st.image(
            foto,
            caption="Vista previa de evidencia",
            use_container_width=True
        )

    if st.button(
        "Guardar Evento",
        use_container_width=True,
        key=f"btn_guardar_evento_{reset_id}"
    ):

        if hora_falla is None:
            st.error(
                "Debes ingresar la hora de falla."
            )
            st.stop()

        if hora_subsanada is None:
            st.error(
                "Debes ingresar la hora subsanada."
            )
            st.stop()

        if tuvo_apoyo and apoyo_1.strip() == "":
            st.error(
                "Seleccionaste que tuvo apoyo, pero no ingresaste Apoyo 1."
            )
            st.stop()

        if apoyo_1 != "" and apoyo_2 != "" and apoyo_1 == apoyo_2:
            st.error(
                "Apoyo 1 y Apoyo 2 no pueden ser el mismo técnico."
            )
            st.stop()

        if (
            causa_preliminar == "REQUIERE REPUESTO"
            and repuesto_requerido.strip() == ""
        ):
            st.error(
                "Debes ingresar el nombre del repuesto requerido."
            )
            st.stop()

        if descripcion.strip() == "":
            st.error(
                "Debes ingresar una descripción de la falla o trabajo realizado."
            )
            st.stop()

        evento_id = generar_id()

        foto_guardada = convertir_foto_base64(
            foto
        )

        datos = [
            evento_id,
            str(fecha_evento),
            tecnico_principal,
            apoyo_1,
            apoyo_2,
            sistema,
            tipo_mantenimiento,
            nivel,
            ubicacion,
            codigo,
            hora_falla_txt,
            hora_subsanada_txt,
            tiempo_parada,
            tipo_falla,
            causa_preliminar,
            repuesto_requerido,
            descripcion,
            estado,
            foto_guardada
        ]

        guardar_bitacora(datos)

        st.success(
            "✅ Evento registrado correctamente. "
            "Puedes registrar otro evento."
        )

        st.session_state.reset_form_evento += 1

        st.rerun()
