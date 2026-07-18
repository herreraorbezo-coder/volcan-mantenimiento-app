# ==========================================================
# LOGIN.PY
# AUTENTICACIÓN POR DNI + RECUPERACIÓN DE SESIÓN
# VOLCAN APP
# ==========================================================

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

import pandas as pd
import streamlit as st

from database import cargar_usuarios
from styles import aplicar_estilos_globales, fondo_login, mostrar_logo


ROLES_VALIDOS = ["ADMIN", "GERENTE", "PLANNER", "TECNICO", "SUPERVISOR"]
DURACION_SESION_SEGUNDOS = 12 * 60 * 60
PARAMETRO_SESION = "volcan_session"


def _clave_sesion() -> bytes:
    """Obtiene la clave usada para firmar el token de sesión.

    En Streamlit Cloud se recomienda agregar en Secrets:
    SESSION_SECRET = "una-clave-larga-y-privada"
    """
    try:
        secreto = st.secrets.get("SESSION_SECRET", "")
    except Exception:
        secreto = ""

    secreto = str(secreto or os.getenv("SESSION_SECRET", "")).strip()

    # Respaldo compatible para no bloquear el despliegue existente.
    # Debe reemplazarse por SESSION_SECRET en Streamlit Secrets.
    if not secreto:
        secreto = "VOLCAN_APP_TICLIO_SESION_2026_CAMBIAR_EN_SECRETS"

    return secreto.encode("utf-8")


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def _crear_token_sesion(dni: str) -> str:
    payload = {
        "dni": str(dni).strip(),
        "iat": int(time.time()),
        "exp": int(time.time()) + DURACION_SESION_SEGUNDOS,
    }
    payload_codificado = _b64_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    firma = hmac.new(
        _clave_sesion(), payload_codificado.encode("utf-8"), hashlib.sha256
    ).digest()
    return f"{payload_codificado}.{_b64_encode(firma)}"


def _validar_token_sesion(token: str) -> Optional[str]:
    try:
        payload_codificado, firma_recibida = str(token).split(".", 1)
        firma_esperada = hmac.new(
            _clave_sesion(), payload_codificado.encode("utf-8"), hashlib.sha256
        ).digest()
        firma_recibida_bytes = _b64_decode(firma_recibida)

        if not hmac.compare_digest(firma_esperada, firma_recibida_bytes):
            return None

        payload = json.loads(_b64_decode(payload_codificado).decode("utf-8"))
        dni = str(payload.get("dni", "")).strip()
        exp = int(payload.get("exp", 0))

        if not dni.isdigit() or len(dni) != 8 or exp <= int(time.time()):
            return None

        return dni
    except Exception:
        return None


def _normalizar_usuarios(df_users: pd.DataFrame) -> pd.DataFrame:
    if df_users is None or df_users.empty:
        return pd.DataFrame()

    df = df_users.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()

    columnas_requeridas = ["dni", "nombre", "rol", "cargo", "empresa", "estado"]
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        raise ValueError(
            "Faltan columnas obligatorias en la hoja usuarios: " + ", ".join(faltantes)
        )

    for col in columnas_requeridas + (["usuario"] if "usuario" in df.columns else []):
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["dni"] = df["dni"].str.replace(".0", "", regex=False).str.strip()
    df["rol"] = df["rol"].str.upper().str.strip()
    df["empresa"] = df["empresa"].str.upper().str.strip()
    df["estado"] = df["estado"].str.upper().str.strip()
    return df


def _buscar_usuario_activo(dni: str):
    df_users = _normalizar_usuarios(cargar_usuarios())
    if df_users.empty:
        return None

    validacion = df_users[
        (df_users["dni"] == str(dni).strip())
        & (df_users["estado"] == "ACTIVO")
        & (df_users["rol"].isin(ROLES_VALIDOS))
    ]

    if validacion.empty:
        return None

    return validacion.iloc[0]


def _cargar_usuario_en_sesion(usuario_data, dni: str) -> None:
    st.session_state.login = True
    st.session_state.dni = str(dni).strip()
    st.session_state.usuario = str(
        usuario_data.get("usuario", dni) if hasattr(usuario_data, "get") else dni
    ).strip() or str(dni).strip()
    st.session_state.nombre = str(usuario_data["nombre"]).strip()
    st.session_state.rol = str(usuario_data["rol"]).upper().strip()
    st.session_state.cargo = str(usuario_data["cargo"]).strip()
    st.session_state.empresa = str(usuario_data["empresa"]).upper().strip()


def _guardar_token_en_url(dni: str) -> None:
    try:
        st.query_params[PARAMETRO_SESION] = _crear_token_sesion(dni)
    except Exception:
        pass


def _eliminar_token_de_url() -> None:
    try:
        if PARAMETRO_SESION in st.query_params:
            del st.query_params[PARAMETRO_SESION]
    except Exception:
        pass


def _recuperar_sesion_desde_url() -> bool:
    try:
        token = st.query_params.get(PARAMETRO_SESION, "")
    except Exception:
        token = ""

    if isinstance(token, list):
        token = token[0] if token else ""

    dni = _validar_token_sesion(str(token)) if token else None
    if not dni:
        if token:
            _eliminar_token_de_url()
        return False

    try:
        usuario_data = _buscar_usuario_activo(dni)
    except Exception:
        # Ante una caída temporal de Google Sheets no se destruye el token.
        return False

    if usuario_data is None:
        _eliminar_token_de_url()
        return False

    _cargar_usuario_en_sesion(usuario_data, dni)
    return True


def obtener_foto_usuario(dni):
    for ext in ["jpg", "jpeg", "png"]:
        ruta = f"assets/fotos_usuarios/{dni}.{ext}"
        if os.path.exists(ruta):
            with open(ruta, "rb") as imagen:
                foto_base64 = base64.b64encode(imagen.read()).decode("utf-8")
            mime = "jpeg" if ext in ["jpg", "jpeg"] else "png"
            return f"data:image/{mime};base64,{foto_base64}"
    return None


def inicializar_sesion():
    valores_iniciales = {
        "login": False,
        "usuario": None,
        "nombre": None,
        "rol": None,
        "cargo": None,
        "dni": None,
        "empresa": None,
        "intento_recuperar_sesion": False,
    }

    for campo, valor in valores_iniciales.items():
        if campo not in st.session_state:
            st.session_state[campo] = valor

    if not st.session_state.login and not st.session_state.intento_recuperar_sesion:
        st.session_state.intento_recuperar_sesion = True
        _recuperar_sesion_desde_url()


def mostrar_login():
    aplicar_estilos_globales()
    fondo_login()

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        mostrar_logo("assets/logo_volcan.png", ancho=260)

    st.markdown(
        """
        <div class="main-title">VOLCAN APP</div>
        <div class="main-subtitle">Sistema Digital de Gestión de Mantenimiento</div>
        <div class="login-line"></div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_login_volcan", clear_on_submit=False):
        dni = st.text_input(
            "DNI",
            placeholder="Ingrese su DNI",
            max_chars=8,
            key="login_dni_input",
        )
        ingresar = st.form_submit_button(
            "Ingresar al sistema", use_container_width=True
        )

    st.markdown(
        """
        <div class="feature-box">
            ⚙️ Bombas &nbsp; | &nbsp; 🚜 Trackless &nbsp; | &nbsp;
            🚛 Lucarbal &nbsp; | &nbsp; 🏗️ Planta Móvil &nbsp; | &nbsp; 📷 Evidencias
        </div>
        <div class="footer-text">Mantenimiento Mecánico · Planeamiento · Confiabilidad</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not ingresar:
        return

    dni = str(dni).strip()
    if not dni:
        st.error("Debe ingresar su DNI.")
        return
    if not dni.isdigit() or len(dni) != 8:
        st.error("El DNI debe tener exactamente 8 dígitos.")
        return

    try:
        usuario_data = _buscar_usuario_activo(dni)
    except ValueError as error:
        st.error(str(error))
        return
    except Exception:
        st.error(
            "No fue posible validar el usuario por una falla temporal de conexión. "
            "Conserve esta pantalla e intente nuevamente."
        )
        return

    if usuario_data is None:
        st.error("DNI no registrado, usuario inactivo o rol no permitido.")
        return

    _cargar_usuario_en_sesion(usuario_data, dni)
    _guardar_token_en_url(dni)
    st.session_state.intento_recuperar_sesion = True
    st.success(f"Bienvenido {st.session_state.nombre}")
    st.rerun()


def cerrar_sesion():
    _eliminar_token_de_url()
    st.session_state.clear()
    st.rerun()


def sidebar_usuario():
    aplicar_estilos_globales()

    with st.sidebar:
        st.markdown("## ⚙️ VOLCAN APP")
        st.markdown("---")

        foto_usuario = obtener_foto_usuario(st.session_state.dni)
        if foto_usuario:
            st.markdown(
                f"""
                <div style="text-align:center;margin-top:8px;margin-bottom:24px;">
                    <img src="{foto_usuario}"
                         style="width:210px;height:210px;object-fit:cover;border-radius:50%;
                                border:4px solid #ffffff;box-shadow:0 10px 28px rgba(0,0,0,.45);">
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.success(st.session_state.nombre)
        st.info(st.session_state.cargo)
        st.info(f"Rol: {st.session_state.rol}")
        st.info(f"Empresa: {st.session_state.empresa}")
        if st.session_state.dni:
            st.caption(f"DNI: {st.session_state.dni}")

        st.caption("Sesión recuperable durante 12 horas en este enlace.")
        st.markdown("---")

        if st.button("Cerrar sesión", use_container_width=True, key="btn_cerrar_sesion"):
            cerrar_sesion()
