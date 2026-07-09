# ==========================================================
# REGISTRO_LUCARBAL.PY
# REGISTRO DE EVENTOS Y ACTIVIDADES DE TALLER LUCARBAL
# ==========================================================

import streamlit as st
import base64

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from zoneinfo import ZoneInfo

from database import (
    cargar_equipos_lucarbal,
    cargar_usuarios,
    guardar_lucarbal_evento,
    guardar_lucarbal_taller,
    generar_id_lucarbal,
    generar_id_lucarbal_taller
)

from config import (
    ESTADOS_LUCARBAL,
    TIPOS_MANTENIMIENTO
)


# ==========================================================
# FECHA Y HORA PERÚ
# ==========================================================

def ahora_peru():
    return datetime.now(ZoneInfo("America/Lima"))


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


def hora_en_rango_turno(turno, hora):
    """Valida si una hora pertenece al turno seleccionado."""

    if hora is None:
        return False

    turno = str(turno).upper().strip()
    minutos = hora.hour * 60 + hora.minute

    # Turno día: 07:00 hasta 18:00
    if turno == "DIA":
        return 7 * 60 <= minutos <= 18 * 60

    # Turno noche: 18:00 hasta 07:00 del día siguiente
    if turno == "NOCHE":
        return minutos >= 18 * 60 or minutos <= 7 * 60

    return False


def mensaje_regla_turno(turno):

    if str(turno).upper().strip() == "DIA":
        return "Turno DIA permitido: 07:00 a 18:00."

    return (
        "Turno NOCHE permitido: 18:00 a 07:00. "
        "Use formato 24 horas. Ejemplo correcto: 21:00 a 23:00."
    )


def validar_horas_por_turno(turno, hora_inicio, hora_fin):
    """Bloquea horas que no correspondan al turno seleccionado."""

    if not hora_en_rango_turno(turno, hora_inicio):
        return False, (
            "La hora de inicio no corresponde al turno seleccionado. "
            + mensaje_regla_turno(turno)
        )

    if not hora_en_rango_turno(turno, hora_fin):
        return False, (
            "La hora final/subsanada no corresponde al turno seleccionado. "
            + mensaje_regla_turno(turno)
        )

    return True, ""


def calcular_horas(fecha, hora_inicio, hora_fin, turno=None):

    inicio = datetime.combine(
        fecha,
        hora_inicio
    )

    fin = datetime.combine(
        fecha,
        hora_fin
    )

    # Si el turno es noche y la hora final es menor o igual a la hora inicial,
    # se entiende que terminó al día siguiente. Ejemplo: 23:00 a 01:00.
    if str(turno).upper().strip() == "NOCHE" and fin <= inicio:
        fin += timedelta(days=1)

    # Compatibilidad con cálculos antiguos sin turno.
    elif turno is None and fin < inicio:
        fin += timedelta(days=1)

    minutos = round(
        (fin - inicio).total_seconds() / 60,
        2
    )

    horas = round(
        minutos / 60,
        2
    )

    return minutos, horas


# ==========================================================
# APOYOS LUCARBAL
# ==========================================================

def obtener_apoyos_lucarbal(tecnico_actual):

    try:
        df_usuarios = cargar_usuarios()

        if df_usuarios.empty:
            return ["SIN APOYO"]

        df_usuarios.columns = (
            df_usuarios.columns
            .str.strip()
            .str.lower()
        )

        columnas_necesarias = [
            "nombre",
            "rol",
            "empresa",
            "estado"
        ]

        for col in columnas_necesarias:
            if col not in df_usuarios.columns:
                return ["SIN APOYO"]

        df_usuarios["nombre"] = df_usuarios["nombre"].astype(str).str.strip()
        df_usuarios["rol"] = df_usuarios["rol"].astype(str).str.upper().str.strip()
        df_usuarios["empresa"] = df_usuarios["empresa"].astype(str).str.upper().str.strip()
        df_usuarios["estado"] = df_usuarios["estado"].astype(str).str.upper().str.strip()

        df_filtrado = df_usuarios[
            (df_usuarios["rol"] == "TECNICO") &
            (df_usuarios["empresa"] == "LUCARBAL") &
            (df_usuarios["estado"] == "ACTIVO")
        ].copy()

        nombres = (
            df_filtrado["nombre"]
            .dropna()
            .unique()
            .tolist()
        )

        nombres = [
            nombre for nombre in nombres
            if nombre.strip() != ""
            and nombre.strip().upper() != tecnico_actual.strip().upper()
        ]

        nombres = sorted(nombres)

        return ["SIN APOYO"] + nombres

    except Exception:
        return ["SIN APOYO"]


# ==========================================================
# REGISTRO LUCARBAL
# ==========================================================

def registro_lucarbal():

    st.title("🚛 REPORTE LUCARBAL")
    st.markdown("---")

    tecnico = str(st.session_state.nombre).strip()
    dni = str(st.session_state.dni).strip()

    apoyos = obtener_apoyos_lucarbal(tecnico)

    tab_mina, tab_taller = st.tabs(
        [
            "🚛 Registro OT / Mina",
            "🏭 Actividades de Taller"
        ]
    )

    # ======================================================
    # TAB 1 - REGISTRO OT / MINA
    # ======================================================

    with tab_mina:

        st.subheader("🚛 REGISTRO DE MANTENIMIENTO EN MINA")

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

        # ==================================================
        # DATOS GENERALES
        # ==================================================

        st.markdown("### 📅 DATOS GENERALES")

        col_fecha, col_turno = st.columns(2)

        with col_fecha:
            fecha = st.date_input(
                "Fecha reporte",
                value=ahora_peru().date(),
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

        # ==================================================
        # APOYOS
        # ==================================================

        st.markdown("### 👥 APOYO TÉCNICO")

        col_apoyo_1, col_apoyo_2 = st.columns(2)

        with col_apoyo_1:
            apoyo_1 = st.selectbox(
                "Apoyo 1",
                apoyos,
                key=f"apoyo_1_luc_{reset_id}"
            )

        with col_apoyo_2:
            apoyo_2 = st.selectbox(
                "Apoyo 2",
                apoyos,
                key=f"apoyo_2_luc_{reset_id}"
            )

        if apoyo_1 != "SIN APOYO" and apoyo_1 == apoyo_2:
            st.warning("⚠️ Apoyo 1 y Apoyo 2 no deben ser la misma persona.")

        # ==================================================
        # EQUIPO
        # ==================================================

        st.markdown("### 🚛 SELECCIÓN DE EQUIPO")

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

        # ==================================================
        # MANTENIMIENTO
        # ==================================================

        tipo_mantenimiento = st.selectbox(
            "Tipo mantenimiento",
            TIPOS_MANTENIMIENTO,
            key=f"tipo_mant_{reset_id}"
        )

        # ==================================================
        # HORAS
        # ==================================================

        st.markdown("### ⏱ REGISTRO DE TIEMPOS")
        st.caption(
            "Para LUCARBAL se registrará solo el tiempo total de parada: "
            "desde que el equipo paró hasta que quedó subsanado."
        )

        if turno == "DIA":
            st.info("🕒 Turno DIA: registre horas entre 07:00 y 18:00.")
        else:
            st.info(
                "🌙 Turno NOCHE: registre en formato 24 horas entre 18:00 y 07:00. "
                "Ejemplo: 21:00 a 23:00, 23:00 a 01:00 o 00:30 a 02:00."
            )

        col_h1, col_h2 = st.columns(2)

        with col_h1:
            hora_falla_input = st.text_input(
                "Hora inicio de parada",
                placeholder="715 → 07:15",
                key=f"hf_{reset_id}"
            )

        with col_h2:
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

        # Se mantienen estas variables vacías por compatibilidad con la hoja actual
        # lucarbal_eventos, que todavía contiene columnas históricas de atención,
        # respuesta y reparación. Ya no se solicitan ni se calculan en el formulario.
        hora_atencion_txt = ""
        tiempo_respuesta = ""
        tiempo_reparacion = ""

        if hora_falla_input:
            st.caption(
                f"Hora inicio de parada detectada: {hora_falla_txt}"
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

            horas_validas, mensaje_validacion = validar_horas_por_turno(
                turno,
                hora_falla,
                hora_sub
            )

            if not horas_validas:
                st.error(mensaje_validacion)
            else:

                _, tiempo_parada = calcular_horas(
                    fecha,
                    hora_falla,
                    hora_sub,
                    turno
                )

                st.metric(
                    "Tiempo total de parada",
                    f"{tiempo_parada} h"
                )

        elif hora_falla_input or hora_sub_input:
            st.warning(
                "Ingrese horas válidas. Ejemplo: 715, 0715 o 07:15"
            )

        # ==================================================
        # REPUESTOS
        # ==================================================

        st.markdown("### 🔩 REPUESTOS")

        requiere_repuesto = st.radio(
            "¿Requiere repuesto?",
            [
                "NO",
                "SI"
            ],
            horizontal=True,
            key=f"req_rep_{reset_id}"
        )

        detalle_repuesto = ""

        if requiere_repuesto == "SI":
            detalle_repuesto = st.text_area(
                "Detalle del repuesto requerido",
                height=90,
                key=f"det_rep_{reset_id}"
            )

        # ==================================================
        # DESCRIPCIÓN
        # ==================================================

        st.markdown("### 📝 DESCRIPCIÓN")

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
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key=f"foto_{reset_id}"
        )

        if foto is not None:
            st.image(
                foto,
                caption="Vista previa",
                use_container_width=True
            )

        # ==================================================
        # GUARDAR EVENTO
        # ==================================================

        if st.button(
            "Guardar Evento Lucarbal",
            use_container_width=True,
            key=f"btn_guardar_lucarbal_{reset_id}"
        ):

            if hora_falla is None:
                st.error("Debes ingresar la hora que paró el equipo.")
                st.stop()

            if hora_sub is None:
                st.error("Debes ingresar la hora subsanada.")
                st.stop()

            if tiempo_parada is None:
                st.error("No se pudo calcular el tiempo total de parada.")
                st.stop()

            horas_validas, mensaje_validacion = validar_horas_por_turno(
                turno,
                hora_falla,
                hora_sub
            )

            if not horas_validas:
                st.error(mensaje_validacion)
                st.stop()

            if descripcion.strip() == "":
                st.error("Debe ingresar descripción.")
                st.stop()

            if requiere_repuesto == "SI" and detalle_repuesto.strip() == "":
                st.error("Debe ingresar el detalle del repuesto requerido.")
                st.stop()

            if apoyo_1 != "SIN APOYO" and apoyo_1 == apoyo_2:
                st.error("Apoyo 1 y Apoyo 2 no pueden ser la misma persona.")
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
                str(ahora_peru()),
                hora_atencion_txt,
                tiempo_respuesta,
                tiempo_reparacion,
                requiere_repuesto,
                detalle_repuesto,
                apoyo_1,
                apoyo_2
            ]

            guardar_lucarbal_evento(
                datos
            )

            st.success(
                "✅ Evento Lucarbal registrado correctamente."
            )

            st.session_state.reset_lucarbal += 1

            st.rerun()

    # ======================================================
    # TAB 2 - ACTIVIDADES DE TALLER
    # ======================================================

    with tab_taller:

        st.subheader("🏭 REGITRO DE ACTIVIDADES EN TALLER")

        if "reset_lucarbal_taller" not in st.session_state:
            st.session_state.reset_lucarbal_taller = 0

        reset_taller = st.session_state.reset_lucarbal_taller

        # ==================================================
        # DATOS GENERALES TALLER
        # ==================================================

        st.markdown("### 📅 DATOS GENERALES")

        col_fecha_t, col_turno_t = st.columns(2)

        with col_fecha_t:
            fecha_taller = st.date_input(
                "Fecha actividad",
                value=ahora_peru().date(),
                key=f"fecha_taller_{reset_taller}"
            )

        with col_turno_t:
            turno_taller = st.selectbox(
                "Turno",
                [
                    "DIA",
                    "NOCHE"
                ],
                key=f"turno_taller_{reset_taller}"
            )

        col_tec_t, col_dni_t = st.columns(2)

        with col_tec_t:
            st.text_input(
                "Técnico responsable",
                value=tecnico,
                disabled=True,
                key=f"tec_taller_{reset_taller}"
            )

        with col_dni_t:
            st.text_input(
                "DNI",
                value=dni,
                disabled=True,
                key=f"dni_taller_{reset_taller}"
            )

        # ==================================================
        # APOYOS TALLER
        # ==================================================

        st.markdown("### 👥 APOYO TÉCNICO")

        col_apoyo_t1, col_apoyo_t2 = st.columns(2)

        with col_apoyo_t1:
            apoyo_1_taller = st.selectbox(
                "Apoyo 1",
                apoyos,
                key=f"apoyo_1_taller_{reset_taller}"
            )

        with col_apoyo_t2:
            apoyo_2_taller = st.selectbox(
                "Apoyo 2",
                apoyos,
                key=f"apoyo_2_taller_{reset_taller}"
            )

        if apoyo_1_taller != "SIN APOYO" and apoyo_1_taller == apoyo_2_taller:
            st.warning("⚠️ Apoyo 1 y Apoyo 2 no deben ser la misma persona.")

        # ==================================================
        # HORAS TALLER
        # ==================================================

        st.markdown("### ⏱ TIEMPO DE ACTIVIDAD")

        if turno_taller == "DIA":
            st.info("🕒 Turno DIA: registre horas entre 07:00 y 18:00.")
        else:
            st.info(
                "🌙 Turno NOCHE: registre en formato 24 horas entre 18:00 y 07:00. "
                "Ejemplo: 21:00 a 23:00, 23:00 a 01:00 o 00:30 a 02:00."
            )

        col_hi, col_hf = st.columns(2)

        with col_hi:
            hora_inicio_input = st.text_input(
                "Hora inicio",
                placeholder="715 → 07:15",
                key=f"hi_taller_{reset_taller}"
            )

        with col_hf:
            hora_fin_input = st.text_input(
                "Hora fin",
                placeholder="930 → 09:30",
                key=f"hf_taller_{reset_taller}"
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

        tiempo_trabajo_min = None

        if hora_inicio and hora_fin:

            horas_validas_taller, mensaje_validacion_taller = validar_horas_por_turno(
                turno_taller,
                hora_inicio,
                hora_fin
            )

            if not horas_validas_taller:
                st.error(mensaje_validacion_taller)
            else:

                tiempo_trabajo_min, tiempo_trabajo_h = calcular_horas(
                    fecha_taller,
                    hora_inicio,
                    hora_fin,
                    turno_taller
                )

                st.info(
                    f"Tiempo trabajado: {tiempo_trabajo_min} min / {tiempo_trabajo_h} h"
                )

        elif hora_inicio_input or hora_fin_input:
            st.warning(
                "Ingrese horas válidas. Ejemplo: 715, 0715 o 07:15"
            )

        # ==================================================
        # DETALLE LIBRE TALLER
        # ==================================================

        st.markdown("### 📝 DETALLE DEL TRABAJO REALIZADO")

        detalle_taller = st.text_area(
            "Detalle de actividad realizada",
            height=180,
            key=f"detalle_taller_{reset_taller}"
        )

        estado_taller = st.selectbox(
            "Estado",
            [
                "FINALIZADO",
                "EN PROCESO",
                "PENDIENTE"
            ],
            key=f"estado_taller_{reset_taller}"
        )

        evidencia_taller = st.file_uploader(
            "Subir evidencia",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key=f"evidencia_taller_{reset_taller}"
        )

        if evidencia_taller is not None:
            st.image(
                evidencia_taller,
                caption="Vista previa",
                use_container_width=True
            )

        # ==================================================
        # GUARDAR TALLER
        # ==================================================

        if st.button(
            "Guardar Actividad de Taller",
            use_container_width=True,
            key=f"btn_guardar_taller_{reset_taller}"
        ):

            if hora_inicio is None:
                st.error("Debes ingresar hora de inicio.")
                st.stop()

            if hora_fin is None:
                st.error("Debes ingresar hora fin.")
                st.stop()

            if tiempo_trabajo_min is None:
                st.error("No se pudo calcular el tiempo trabajado.")
                st.stop()

            horas_validas_taller, mensaje_validacion_taller = validar_horas_por_turno(
                turno_taller,
                hora_inicio,
                hora_fin
            )

            if not horas_validas_taller:
                st.error(mensaje_validacion_taller)
                st.stop()

            if detalle_taller.strip() == "":
                st.error("Debe ingresar el detalle de la actividad realizada.")
                st.stop()

            if apoyo_1_taller != "SIN APOYO" and apoyo_1_taller == apoyo_2_taller:
                st.error("Apoyo 1 y Apoyo 2 no pueden ser la misma persona.")
                st.stop()

            id_taller = generar_id_lucarbal_taller()

            evidencia_base64 = convertir_foto_base64(
                evidencia_taller
            )

            datos_taller = [
                id_taller,
                str(fecha_taller),
                turno_taller,
                tecnico,
                apoyo_1_taller,
                apoyo_2_taller,
                hora_inicio_txt,
                hora_fin_txt,
                tiempo_trabajo_min,
                "",
                detalle_taller,
                estado_taller,
                evidencia_base64,
                str(ahora_peru())
            ]

            guardar_lucarbal_taller(
                datos_taller
            )

            st.success(
                "✅ Actividad de taller registrada correctamente."
            )

            st.session_state.reset_lucarbal_taller += 1

            st.rerun()
