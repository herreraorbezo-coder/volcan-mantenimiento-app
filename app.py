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

# ==========================================================
# BOMBEO
# ==========================================================

from registro_ot import registro_ot
from dashboard import mostrar_dashboard
from historial_eventos import mostrar_historial_eventos

# ==========================================================
# TRACKLESS
# ==========================================================

from registro_trackless import registro_trackless
from dashboard_trackless import mostrar_dashboard_trackless

# ==========================================================
# LUCARBAL
# ==========================================================

from registro_lucarbal import registro_lucarbal
from historial_lucarbal import mostrar_historial_lucarbal
from dashboard_lucarbal import mostrar_dashboard_lucarbal

# ==========================================================
# PLANTA MÓVIL - LIVERH
# ==========================================================

from registro_planta_movil import registro_planta_movil
from registro_despacho_mixers import registro_despacho_mixers
from historial_planta_movil import mostrar_historial_planta_movil
from historial_despacho_mixers import mostrar_historial_despacho_mixers


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
# SIDEBAR
# ==========================================================

sidebar_usuario()


# ==========================================================
# VARIABLES
# ==========================================================

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
        "Historial Lucarbal",
        "Dashboard Lucarbal",

        "Registro Mantto Planta Móvil",
        "Historial Mantto Planta Móvil",
        "Registro Despacho Mixers",
        "Historial Despacho Mixers"
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
            "Historial Lucarbal",
            "Dashboard Lucarbal"
        ]

    else:

        opciones_menu = [
            "Historial Lucarbal"
        ]


# ==========================================================
# LIVERH - PLANTA MÓVIL
# ==========================================================

elif empresa == "LIVERH":

    if rol == "TECNICO":

        opciones_menu = [
            "Registro Mantto Planta Móvil",
            "Historial Mantto Planta Móvil"
        ]

    elif rol == "SUPERVISOR":

        opciones_menu = [
            "Registro Despacho Mixers",
            "Historial Despacho Mixers",
            "Historial Mantto Planta Móvil"
        ]

    elif rol in ["ADMIN", "PLANNER"]:

        opciones_menu = [
            "Registro Mantto Planta Móvil",
            "Historial Mantto Planta Móvil",
            "Registro Despacho Mixers",
            "Historial Despacho Mixers"
        ]

    else:

        opciones_menu = [
            "Historial Mantto Planta Móvil"
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


# ==========================================================
# FALLBACK
# ==========================================================

else:

    opciones_menu = [
        "Historial Eventos"
    ]


# ==========================================================
# MENÚ
# ==========================================================

menu = st.sidebar.radio(
    "Menú",
    opciones_menu
)


# ==========================================================
# PANTALLAS - BOMBEO
# ==========================================================

if menu == "Registro Evento":

    registro_ot()

elif menu == "Historial Eventos":

    mostrar_historial_eventos()

elif menu == "Dashboard":

    if rol in ["ADMIN", "PLANNER"] or dni == DNI_ADMIN_TRACKLESS:
        mostrar_dashboard()
    else:
        st.error("No tienes permisos.")


# ==========================================================
# PANTALLAS - TRACKLESS
# ==========================================================

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


# ==========================================================
# PANTALLAS - LUCARBAL
# ==========================================================

elif menu == "Registro Lucarbal":

    if (
        empresa == "LUCARBAL"
        and rol == "TECNICO"
    ) or dni == DNI_ADMIN_TRACKLESS:

        registro_lucarbal()

    else:

        st.error("Solo técnicos Lucarbal pueden registrar eventos.")

elif menu == "Historial Lucarbal":

    if empresa == "LUCARBAL" or dni == DNI_ADMIN_TRACKLESS:
        mostrar_historial_lucarbal()
    else:
        st.error("No tienes permisos para ver Historial Lucarbal.")

elif menu == "Dashboard Lucarbal":

    if (
        empresa == "LUCARBAL"
        and rol in ["PLANNER", "ADMIN"]
    ) or dni == DNI_ADMIN_TRACKLESS:

        mostrar_dashboard_lucarbal()

    else:

        st.error("No tienes permisos para ver Dashboard Lucarbal.")


# ==========================================================
# PANTALLAS - PLANTA MÓVIL / LIVERH
# ==========================================================

elif menu == "Registro Mantto Planta Móvil":

    if (
        empresa == "LIVERH"
        and rol in ["TECNICO", "ADMIN", "PLANNER"]
    ) or dni == DNI_ADMIN_TRACKLESS:

        registro_planta_movil()

    else:

        st.error("No tienes permisos para registrar mantenimiento de Planta Móvil.")

elif menu == "Historial Mantto Planta Móvil":

    if (
        empresa == "LIVERH"
        and rol in ["TECNICO", "SUPERVISOR", "ADMIN", "PLANNER"]
    ) or dni == DNI_ADMIN_TRACKLESS:

        mostrar_historial_planta_movil()

    else:

        st.error("No tienes permisos para ver el historial de Planta Móvil.")

elif menu == "Registro Despacho Mixers":

    if (
        empresa == "LIVERH"
        and rol in ["SUPERVISOR", "ADMIN", "PLANNER"]
    ) or dni == DNI_ADMIN_TRACKLESS:

        registro_despacho_mixers()

    else:

        st.error("No tienes permisos para registrar despacho de mixers.")

elif menu == "Historial Despacho Mixers":

    if (
        empresa == "LIVERH"
        and rol in ["SUPERVISOR", "ADMIN", "PLANNER"]
    ) or dni == DNI_ADMIN_TRACKLESS:

        mostrar_historial_despacho_mixers()

    else:

        st.error("No tienes permisos para ver el historial de despacho de mixers.")
