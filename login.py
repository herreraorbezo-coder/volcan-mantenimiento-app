# ==========================================================
# LOGIN.PY
# LOGIN POR DNI - VOLCAN APP
# ==========================================================

import streamlit as st
import os
import base64

from database import cargar_usuarios
from styles import (
    aplicar_estilos_globales,
    fondo_login,
    mostrar_logo
)


# ==========================================================
# ROLES VÁLIDOS
# ==========================================================

ROLES_VALIDOS = [
    "ADMIN",
    "GERENTE",
    "PLANNER",
    "TECNICO",
    "SUPERVISOR"
]


# ==========================================================
# FOTO USUARIO
# ==========================================================

def obtener_foto_usuario(dni):

    extensiones = [
        "jpg",
        "jpeg",
        "png"
    ]

    for ext in extensiones:

        ruta = f"assets/fotos_usuarios/{dni}.{ext}"

        if os.path.exists(ruta):

            with open(ruta, "rb") as imagen:

                foto_base64 = base64.b64encode(
                    imagen.read()
                ).decode("utf-8")

            return f"data:image/{ext};base64,{foto_base64}"

    return None


# ==========================================================
# INICIALIZAR SESSION STATE
# ==========================================================

def inicializar_sesion():

    campos = [
        "login",
        "usuario",
        "nombre",
        "rol",
        "cargo",
        "dni",
        "empresa"
    ]

    for campo in campos:

        if campo not in st.session_state:

            if campo == "login":
                st.session_state[campo] = False
            else:
                st.session_state[campo] = None


# ==========================================================
# LOGIN
# ==========================================================

def mostrar_login():

    aplicar_estilos_globales()
    fondo_login()

    st.markdown(
        '<div class="login-card">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:

        mostrar_logo(
            "assets/logo_volcan.png",
            ancho=260
        )

    st.markdown(
        """
        <div class="main-title">
            VOLCAN APP
        </div>

        <div class="main-subtitle">
            Sistema Digital de Gestión de Mantenimiento
        </div>

        <div class="login-line"></div>
        """,
        unsafe_allow_html=True
    )

    dni = st.text_input(
        "DNI",
        placeholder="Ingrese su DNI",
        max_chars=8
    )

    ingresar = st.button(
        "Ingresar al sistema",
        use_container_width=True
    )

    st.markdown(
        """
        <div class="feature-box">
            ⚙️ Bombas &nbsp; | &nbsp;
            🚜 Trackless &nbsp; | &nbsp;
            🚛 Lucarbal &nbsp; | &nbsp;
            🏗️ Planta Móvil &nbsp; | &nbsp;
            📷 Evidencias
        </div>

        <div class="footer-text">
            Mantenimiento Mecánico · Planeamiento · Confiabilidad
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    if ingresar:

        dni = str(dni).strip()

        if dni == "":

            st.error(
                "Debe ingresar su DNI."
            )

            st.stop()

        if not dni.isdigit() or len(dni) != 8:

            st.error(
                "El DNI debe tener 8 dígitos."
            )

            st.stop()

        df_users = cargar_usuarios()

        df_users.columns = (
            df_users.columns
            .str.strip()
            .str.lower()
        )

        columnas_requeridas = [
            "dni",
            "nombre",
            "rol",
            "cargo",
            "empresa",
            "estado"
        ]

        for col in columnas_requeridas:

            if col not in df_users.columns:

                st.error(
                    f"Falta la columna '{col}' en usuarios."
                )

                st.stop()

        for col in [
            "dni",
            "nombre",
            "rol",
            "cargo",
            "empresa",
            "estado"
        ]:

            df_users[col] = (
                df_users[col]
                .astype(str)
                .str.strip()
            )

        df_users["dni"] = (
            df_users["dni"]
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

        df_users["rol"] = (
            df_users["rol"]
            .str.upper()
            .str.strip()
        )

        df_users["empresa"] = (
            df_users["empresa"]
            .str.upper()
            .str.strip()
        )

        df_users["estado"] = (
            df_users["estado"]
            .str.upper()
            .str.strip()
        )

        usuarios_rol_invalido = df_users[
            ~df_users["rol"].isin(
                ROLES_VALIDOS
            )
        ]

        if not usuarios_rol_invalido.empty:

            st.warning(
                "⚠️ Existen usuarios con rol no válido en la hoja usuarios. "
                "Roles permitidos: ADMIN, GERENTE, PLANNER, TECNICO, SUPERVISOR."
            )

        validacion = df_users[
            (df_users["dni"] == dni)
            &
            (df_users["estado"] == "ACTIVO")
            &
            (
                df_users["rol"].isin(
                    ROLES_VALIDOS
                )
            )
        ]

        if not validacion.empty:

            usuario_data = validacion.iloc[0]

            st.session_state.login = True
            st.session_state.dni = dni

            if "usuario" in df_users.columns:

                st.session_state.usuario = str(
                    usuario_data["usuario"]
                ).strip()

            else:

                st.session_state.usuario = dni

            st.session_state.nombre = str(
                usuario_data["nombre"]
            ).strip()

            st.session_state.rol = str(
                usuario_data["rol"]
            ).upper().strip()

            st.session_state.cargo = str(
                usuario_data["cargo"]
            ).strip()

            st.session_state.empresa = str(
                usuario_data["empresa"]
            ).upper().strip()

            st.success(
                f"Bienvenido {st.session_state.nombre}"
            )

            st.rerun()

        else:

            st.error(
                "DNI no registrado, usuario inactivo o rol no permitido."
            )


# ==========================================================
# SIDEBAR
# ==========================================================

def sidebar_usuario():

    aplicar_estilos_globales()

    with st.sidebar:

        st.markdown(
            "## ⚙️ VOLCAN APP"
        )

        st.markdown("---")

        foto_usuario = obtener_foto_usuario(
            st.session_state.dni
        )

        if foto_usuario:

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    margin-top: 8px;
                    margin-bottom: 24px;
                ">
                    <img src="{foto_usuario}"
                         style="
                            width:210px;
                            height:210px;
                            object-fit:cover;
                            border-radius:50%;
                            border:4px solid #ffffff;
                            box-shadow:0px 10px 28px rgba(0,0,0,0.45);
                         ">
                </div>
                """,
                unsafe_allow_html=True
            )

        st.success(
            st.session_state.nombre
        )

        st.info(
            st.session_state.cargo
        )

        st.info(
            f"Rol: {st.session_state.rol}"
        )

        st.info(
            f"Empresa: {st.session_state.empresa}"
        )

        if st.session_state.dni:

            st.caption(
                f"DNI: {st.session_state.dni}"
            )

        st.markdown("---")

        if st.button(
            "Cerrar sesión",
            use_container_width=True
        ):

            st.session_state.clear()

            st.rerun()
