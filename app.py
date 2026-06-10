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
from historial_eventos import mostrar_historial_eventos

from registro_trackless import registro_trackless
from dashboard_trackless import mostrar_dashboard_trackless


# ==========================================================
# CONFIGURACIÓN APP
# ==========================================================

st.set_page_config(
    page_title="MANTENIMIENTO VOLCAN",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
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

DNI_ADMIN_TRACKLESS = "75394588"

if rol == "ADMIN":

    opciones_menu = [
        "Registro Evento",
        "Historial Eventos",
        "Dashboard"
    ]

elif rol == "PLANNER":

    opciones_menu = [
        "Registro Evento",
        "Historial Eventos",
        "Dashboard"
    ]

elif rol == "TECNICO":

    opciones_menu = [
        "Registro Evento",
        "Historial Eventos"
    ]

else:

    opciones_menu = [
        "Registro Evento",
        "Historial Eventos"
    ]


# ==========================================================
# MENÚ TRACKLESS SOLO PARA JHAN
# ==========================================================

if st.session_state.dni == DNI_ADMIN_TRACKLESS:

    opciones_menu += [
        "Registro Trackless",
        "Dashboard Trackless"
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

elif menu == "Historial Eventos":

    mostrar_historial_eventos()

elif menu == "Dashboard":

    if rol in ["ADMIN", "PLANNER"]:

        mostrar_dashboard()

    else:

        st.error(
            "No tienes permisos para acceder al Dashboard."
        )

elif menu == "Registro Trackless":

    if st.session_state.dni == DNI_ADMIN_TRACKLESS:

        registro_trackless()

    else:

        st.error(
            "No tienes permisos para acceder a Trackless."
        )

elif menu == "Dashboard Trackless":

    if st.session_state.dni == DNI_ADMIN_TRACKLESS:

        mostrar_dashboard_trackless()

    else:

        st.error(
            "No tienes permisos para acceder al Dashboard Trackless."
        )
