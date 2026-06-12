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

from registro_lucarbal import registro_lucarbal
from historial_lucarbal import mostrar_historial_lucarbal


st.set_page_config(
    page_title="MANTENIMIENTO VOLCAN",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

inicializar_sesion()

if not st.session_state.login:
    mostrar_login()
    st.stop()

sidebar_usuario()

rol = str(st.session_state.rol).upper().strip()
empresa = str(st.session_state.empresa).upper().strip()
dni = str(st.session_state.dni).strip()

DNI_ADMIN_TRACKLESS = "75394588"
opciones_menu = []


# ==========================================================
# JHAN: ACCESO TOTAL
# ==========================================================

if dni == DNI_ADMIN_TRACKLESS:
    opciones_menu = [
        "Registro Evento",
        "Historial Eventos",
        "Dashboard",
        "Registro Trackless",
        "Dashboard Trackless",
        "Registro Lucarbal",
        "Historial Lucarbal"
    ]


# ==========================================================
# LUCARBAL
# ==========================================================

elif empresa == "LUCARBAL":

    if rol == "TECNICO":
        opciones_menu = [
            "Registro Lucarbal",
            "Historial Lucarbal"
        ]

    elif rol in ["PLANNER", "ADMIN"]:
        opciones_menu = [
            "Historial Lucarbal"
        ]

    else:
        opciones_menu = [
            "Historial Lucarbal"
        ]


# ==========================================================
# VOLCAN
# ==========================================================

elif empresa == "VOLCAN":

    if rol in ["ADMIN", "PLANNER"]:
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

else:
    opciones_menu = ["Historial Eventos"]


menu = st.sidebar.radio("Menú", opciones_menu)


if menu == "Registro Evento":
    registro_ot()

elif menu == "Historial Eventos":
    mostrar_historial_eventos()

elif menu == "Dashboard":
    if rol in ["ADMIN", "PLANNER"] or dni == DNI_ADMIN_TRACKLESS:
        mostrar_dashboard()
    else:
        st.error("No tienes permisos.")

elif menu == "Registro Trackless":
    if dni == DNI_ADMIN_TRACKLESS:
        registro_trackless()
    else:
        st.error("No tienes permisos para Trackless.")

elif menu == "Dashboard Trackless":
    if dni == DNI_ADMIN_TRACKLESS:
        mostrar_dashboard_trackless()
    else:
        st.error("No tienes permisos para Trackless.")

elif menu == "Registro Lucarbal":
    if (empresa == "LUCARBAL" and rol == "TECNICO") or dni == DNI_ADMIN_TRACKLESS:
        registro_lucarbal()
    else:
        st.error("Solo técnicos Lucarbal pueden registrar eventos.")

elif menu == "Historial Lucarbal":
    if empresa == "LUCARBAL" or dni == DNI_ADMIN_TRACKLESS:
        mostrar_historial_lucarbal()
    else:
        st.error("No tienes permisos para ver Historial Lucarbal.")
