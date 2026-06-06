# ==========================================================
# LOGIN.PY
# LOGIN POR DNI - VOLCAN APP
# ==========================================================

import streamlit as st

from database import cargar_usuarios
from styles import aplicar_estilos_globales, fondo_login, mostrar_logo


# ==========================================================
# INICIALIZAR SESSION STATE
# ==========================================================

def inicializar_sesion():

    if "login" not in st.session_state:
        st.session_state.login = False

    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    if "nombre" not in st.session_state:
        st.session_state.nombre = None

    if "rol" not in st.session_state:
        st.session_state.rol = None

    if "cargo" not in st.session_state:
        st.session_state.cargo = None

    if "dni" not in st.session_state:
        st.session_state.dni = None


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

    # LOGO CENTRADO
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        mostrar_logo(
            "assets/logo_volcan.png",
            ancho=260
        )

    st.markdown(
        """
        <div class="main-title">VOLCAN APP</div>
        <div class="main-subtitle">
            Sistema Digital de Gestión de Eventos de Bombeo
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
            ⚙️ Registro de eventos &nbsp; | &nbsp;
            💧 Sistema de bombeo &nbsp; | &nbsp;
            📊 KPIs & Pareto &nbsp; | &nbsp;
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

        dni = dni.strip()

        if dni == "":
            st.error("Debe ingresar su DNI.")
            st.stop()

        if not dni.isdigit() or len(dni) != 8:
            st.error("El DNI debe tener 8 dígitos numéricos.")
            st.stop()

        df_users = cargar_usuarios()

        df_users.columns = (
            df_users.columns
            .str.strip()
            .str.lower()
        )

        if "dni" not in df_users.columns:
            st.error("La hoja usuarios no tiene la columna 'dni'.")
            st.stop()

        columnas_requeridas = [
            "dni",
            "nombre",
            "rol",
            "cargo",
            "estado"
        ]

        for col in columnas_requeridas:
            if col not in df_users.columns:
                st.error(f"Falta la columna '{col}' en la hoja usuarios.")
                st.stop()

        for col in ["dni", "estado"]:
            df_users[col] = (
                df_users[col]
                .astype(str)
                .str.strip()
            )

        validacion = df_users[

            (df_users["dni"] == dni) &

            (df_users["estado"].str.upper() == "ACTIVO")
        ]

        if not validacion.empty:

            usuario_data = validacion.iloc[0]

            st.session_state.login = True
            st.session_state.dni = dni

            if "usuario" in df_users.columns:
                st.session_state.usuario = usuario_data["usuario"]
            else:
                st.session_state.usuario = dni

            st.session_state.nombre = usuario_data["nombre"]
            st.session_state.rol = usuario_data["rol"]
            st.session_state.cargo = usuario_data["cargo"]

            st.success(
                f"Bienvenido {usuario_data['nombre']}"
            )

            st.rerun()

        else:

            st.error(
                "DNI no registrado o usuario inactivo."
            )


# ==========================================================
# SIDEBAR USUARIO
# ==========================================================

def sidebar_usuario():

    aplicar_estilos_globales()

    with st.sidebar:

        st.markdown("## ⚙️ VOLCAN APP")
        st.markdown("---")

        st.success(
            st.session_state.nombre
        )

        st.info(
            st.session_state.cargo
        )

        st.info(
            f"Rol: {st.session_state.rol}"
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
