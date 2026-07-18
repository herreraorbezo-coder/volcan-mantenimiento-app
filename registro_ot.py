# ==========================================================
# REGISTRO_OT.PY
# REGISTRO DE EVENTO / FALLA DE BOMBA + TALLER VOLCAN
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from zoneinfo import ZoneInfo

from database import (
    cargar_equipos,
    guardar_bitacora,
    guardar_volcan_taller,
    generar_id,
    generar_id_volcan_taller
)

from config import (
    ESTADOS,
    ESTADOS_TALLER_VOLCAN,
    EMPRESAS_APOYO_VOLCAN,
    AREAS_APOYO_VOLCAN
)


# ==========================================================
# FECHA / HORA PERÚ
# ==========================================================

def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


def validar_archivo_imagen(archivo, limite_mb=8):
    """Valida tamaño y tipo antes de procesar la evidencia."""
    if archivo is None:
        return True, ""

    nombre = str(getattr(archivo, "name", "")).lower()
    if not nombre.endswith((".jpg", ".jpeg", ".png")):
        return False, "Formato no permitido. Use JPG, JPEG o PNG."

    tamanio = int(getattr(archivo, "size", 0) or 0)
    if tamanio > limite_mb * 1024 * 1024:
        return False, (
            f"La imagen pesa más de {limite_mb} MB. "
            "Redúzcala o tome una foto con menor resolución."
        )

    return True, ""


def guardar_seguro(funcion_guardado, datos, bandera):
    """Evita doble envío y conserva el formulario cuando Google Sheets falla."""
    if st.session_state.get(bandera, False):
        st.warning("El registro ya se está procesando. Espere unos segundos.")
        return False

    st.session_state[bandera] = True
    try:
        funcion_guardado(datos)
        return True
    except Exception as error:
        st.error(
            "No se pudo guardar el registro. Los datos del formulario se mantienen "
            "para que pueda intentarlo nuevamente. Detalle: " + str(error)
        )
        return False
    finally:
        st.session_state[bandera] = False


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
# CALCULAR HORAS
# ==========================================================

def calcular_horas(fecha, hora_inicio, hora_fin):

    inicio = datetime.combine(
        fecha,
        hora_inicio
    )

    fin = datetime.combine(
        fecha,
        hora_fin
    )

    if fin < inicio:
        fin += timedelta(days=1)

    horas = round(
        (fin - inicio).total_seconds() / 3600,
        2
    )

    return horas


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
# TAB EVENTO BOMBEO
# ==========================================================

def mostrar_registro_bombeo(reset_id):

    df_equipos = cargar_equipos()

    df_equipos.columns = (
        df_equipos.columns
        .str.strip()
        .str.lower()
    )

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

        tiempo_parada = calcular_horas(
            fecha_evento,
            hora_falla,
            hora_subsanada
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

        if not guardar_seguro(
            guardar_bitacora,
            datos,
            "guardando_evento_bombeo"
        ):
            st.stop()

        st.success(
            "✅ Evento registrado correctamente. "
            "Puedes registrar otro evento."
        )

        st.session_state.reset_form_evento += 1

        st.rerun()


# ==========================================================
# TAB ACTIVIDADES TALLER / APOYO VOLCAN
# ==========================================================

def mostrar_registro_taller_volcan(reset_id):

    st.markdown("### 🏭 Actividades Taller / Apoyo Volcan")

    tecnico_principal = str(st.session_state.nombre).strip()

    col_fecha, col_turno = st.columns(2)

    with col_fecha:

        fecha_actividad = st.date_input(
            "Fecha actividad",
            value=ahora_peru().date(),
            key=f"fecha_taller_volcan_{reset_id}"
        )

    with col_turno:

        turno = st.selectbox(
            "Turno",
            [
                "DIA",
                "NOCHE"
            ],
            key=f"turno_taller_volcan_{reset_id}"
        )

    col_tec, col_empresa = st.columns(2)

    with col_tec:

        st.text_input(
            "Técnico responsable",
            value=tecnico_principal,
            disabled=True,
            key=f"tecnico_taller_volcan_{reset_id}"
        )

    with col_empresa:

        empresa_apoyada = st.selectbox(
            "Empresa / área apoyada",
            EMPRESAS_APOYO_VOLCAN,
            key=f"empresa_apoyada_volcan_{reset_id}"
        )

    area_apoyo = st.selectbox(
        "Área / tipo de apoyo",
        AREAS_APOYO_VOLCAN,
        key=f"area_apoyo_volcan_{reset_id}"
    )

    st.markdown("### 👥 Apoyo técnico")

    apoyo_1 = ""
    apoyo_2 = ""

    tuvo_apoyo = st.checkbox(
        "¿Tuvo apoyo de otro técnico?",
        key=f"tuvo_apoyo_taller_volcan_{reset_id}"
    )

    if tuvo_apoyo:

        apoyos_disponibles = obtener_apoyos_disponibles(
            tecnico_principal
        )

        col_ap1, col_ap2 = st.columns(2)

        with col_ap1:

            apoyo_1 = st.selectbox(
                "Apoyo 1",
                [""] + apoyos_disponibles,
                key=f"apoyo_1_taller_volcan_{reset_id}"
            )

        apoyos_para_apoyo2 = [
            tecnico
            for tecnico in apoyos_disponibles
            if tecnico != apoyo_1
        ]

        with col_ap2:

            apoyo_2 = st.selectbox(
                "Apoyo 2",
                [""] + apoyos_para_apoyo2,
                key=f"apoyo_2_taller_volcan_{reset_id}"
            )

    st.markdown("### ⏱ Tiempo trabajado")

    col_h1, col_h2 = st.columns(2)

    with col_h1:

        hora_inicio_input = st.text_input(
            "Hora inicio",
            placeholder="Ejemplo: 800 → 08:00",
            key=f"hora_inicio_taller_volcan_{reset_id}"
        )

    with col_h2:

        hora_fin_input = st.text_input(
            "Hora fin",
            placeholder="Ejemplo: 1030 → 10:30",
            key=f"hora_fin_taller_volcan_{reset_id}"
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

    tiempo_trabajo_h = None

    if hora_inicio and hora_fin:

        tiempo_trabajo_h = calcular_horas(
            fecha_actividad,
            hora_inicio,
            hora_fin
        )

        st.info(
            f"Tiempo trabajado: {tiempo_trabajo_h} horas"
        )

    elif hora_inicio_input or hora_fin_input:

        st.warning(
            "Ingrese hora válida. Ejemplo: 800, 0800 o 08:00"
        )

    st.markdown("### 📝 Detalle de actividad")

    detalle = st.text_area(
        "Detalle del trabajo realizado",
        height=160,
        placeholder=(
            "Ejemplo: Apoyo en soldadura, fabricación de varillas, "
            "corte de material, apoyo a contrata, apoyo a mantenimiento eléctrico..."
        ),
        key=f"detalle_taller_volcan_{reset_id}"
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS_TALLER_VOLCAN,
        key=f"estado_taller_volcan_{reset_id}"
    )

    evidencia = st.file_uploader(
        "Subir evidencia fotográfica",
        type=["jpg", "jpeg", "png"],
        key=f"evidencia_taller_volcan_{reset_id}"
    )

    if evidencia is not None:

        st.image(
            evidencia,
            caption="Vista previa de evidencia",
            use_container_width=True
        )

    if st.button(
        "Guardar Actividad Taller / Apoyo",
        use_container_width=True,
        key=f"btn_guardar_taller_volcan_{reset_id}"
    ):

        if hora_inicio is None:
            st.error(
                "Debes ingresar la hora de inicio."
            )
            st.stop()

        if hora_fin is None:
            st.error(
                "Debes ingresar la hora fin."
            )
            st.stop()

        if tiempo_trabajo_h is None:
            st.error(
                "No se pudo calcular el tiempo trabajado."
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

        if detalle.strip() == "":
            st.error(
                "Debes ingresar el detalle del trabajo realizado."
            )
            st.stop()

        id_taller = generar_id_volcan_taller()

        evidencia_guardada = convertir_foto_base64(
            evidencia
        )

        datos = [
            id_taller,
            str(fecha_actividad),
            turno,
            tecnico_principal,
            apoyo_1,
            apoyo_2,
            empresa_apoyada,
            area_apoyo,
            hora_inicio_txt,
            hora_fin_txt,
            tiempo_trabajo_h,
            detalle,
            estado,
            evidencia_guardada,
            str(ahora_peru())
        ]

        if not guardar_seguro(
            guardar_volcan_taller,
            datos,
            "guardando_taller_volcan"
        ):
            st.stop()

        st.success(
            "✅ Actividad de taller / apoyo registrada correctamente."
        )

        st.session_state.reset_form_evento += 1

        st.rerun()


# ==========================================================
# REGISTRO OT PRINCIPAL
# ==========================================================

def registro_ot():

    st.title("⚙️ Registro Mantenimiento Volcan")
    st.markdown("---")

    if "reset_form_evento" not in st.session_state:
        st.session_state.reset_form_evento = 0

    reset_id = st.session_state.reset_form_evento

    tab_bombeo, tab_taller = st.tabs([
        "⚙️ Registro Evento Bombas",
        "🏭 Actividades Taller / Apoyo"
    ])

    with tab_bombeo:

        mostrar_registro_bombeo(reset_id)

    with tab_taller:

        mostrar_registro_taller_volcan(reset_id)
