# ==========================================================
# APP.PY
# VOLCAN APP
# ==========================================================

import streamlit as st

from login import (
    inicializar_sesion,
    mostrar_login,
    sidebar_usuario
)

from registro_ot import registro_ot
from dashboard import mostrar_dashboard


# ==========================================================
# CONFIGURACIÓN APP
# ==========================================================

st.set_page_config(
    page_title="VOLCAN APP",
    page_icon="⚙️",
    layout="wide"
)


# ==========================================================
# INICIALIZAR SESIÓN
# ==========================================================

inicializar_sesion()


# ==========================================================
# LOGIN
# ==========================================================

if not st.session_state.login:

    mostrar_login()

    st.stop()


# ==========================================================
# SIDEBAR USUARIO
# ==========================================================

sidebar_usuario()


# ==========================================================
# MENÚ SEGÚN ROL
# ==========================================================

rol = st.session_state.rol.upper().strip()

if rol == "ADMIN":

    opciones_menu = [
        "Registro Evento",
        "Dashboard"
    ]

elif rol == "PLANNER":

    opciones_menu = [
        "Registro Evento",
        "Dashboard"
    ]

elif rol == "TECNICO":

    opciones_menu = [
        "Registro Evento"
    ]

else:

    opciones_menu = [
        "Registro Evento"
    ]


menu = st.sidebar.radio(
    "Menú",
    opciones_menu
)


# ==========================================================
# PANTALLAS
# ==========================================================

if menu == "Registro Evento":

    registro_ot()

elif menu == "Dashboard":

    if rol in ["ADMIN", "PLANNER"]:

        mostrar_dashboard()

    else:

        st.error(
            "No tienes permisos para acceder al Dashboard."
        )