# ==========================================================
# APP.PY
# VOLCAN APP - CONTROL DE ACCESO POR EMPRESA Y ROL
# ==========================================================

import streamlit as st

from login import inicializar_sesion, mostrar_login, sidebar_usuario

from registro_ot import registro_ot
from dashboard import mostrar_dashboard
from historial_eventos import mostrar_historial_eventos

from registro_trackless import registro_trackless
from dashboard_trackless import mostrar_dashboard_trackless

from registro_lucarbal import registro_lucarbal
from historial_lucarbal import mostrar_historial_lucarbal
from dashboard_lucarbal import mostrar_dashboard_lucarbal
from editar_registros import editar_registros

from registro_planta_movil import registro_planta_movil
from registro_despacho_mixers import registro_despacho_mixers
from historial_planta_movil import mostrar_historial_planta_movil
from historial_despacho_mixers import mostrar_historial_despacho_mixers


st.set_page_config(
    page_title="MANTENIMIENTO VOLCAN",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inicializar_sesion()

if not st.session_state.login:
    mostrar_login()
    st.stop()

sidebar_usuario()

rol = str(st.session_state.get("rol", "")).upper().strip()
empresa = str(st.session_state.get("empresa", "")).upper().strip()
dni = str(st.session_state.get("dni", "")).strip()

DNI_ADMIN_GENERAL = "75394588"
ACCESO_TOTAL = dni == DNI_ADMIN_GENERAL or rol in ["ADMIN", "GERENTE"]


def _menu_por_usuario():
    if ACCESO_TOTAL:
        return [
            "Registro Evento",
            "Historial Eventos",
            "Dashboard",
            "Registro Trackless",
            "Dashboard Trackless",
            "Registro Lucarbal",
            "Historial Lucarbal",
            "Dashboard Lucarbal",
            "Editar Reportes",
            "Registro Mantto Planta Móvil",
            "Historial Mantto Planta Móvil",
            "Registro Despacho Mixers",
            "Historial Despacho Mixers",
        ]

    if empresa == "LUCARBAL":
        if rol == "TECNICO":
            return ["Registro Lucarbal", "Historial Lucarbal", "Editar Reportes"]
        if rol == "PLANNER":
            return ["Historial Lucarbal", "Dashboard Lucarbal"]
        if rol == "SUPERVISOR":
            return ["Historial Lucarbal", "Dashboard Lucarbal"]
        return ["Historial Lucarbal"]

    if empresa == "LIVERH":
        if rol == "TECNICO":
            return ["Registro Mantto Planta Móvil", "Historial Mantto Planta Móvil"]
        if rol == "SUPERVISOR":
            return [
                "Registro Despacho Mixers",
                "Historial Despacho Mixers",
                "Historial Mantto Planta Móvil",
            ]
        if rol == "PLANNER":
            return [
                "Registro Mantto Planta Móvil",
                "Historial Mantto Planta Móvil",
                "Registro Despacho Mixers",
                "Historial Despacho Mixers",
            ]
        return ["Historial Mantto Planta Móvil"]

    if empresa == "VOLCAN":
        if rol == "PLANNER":
            return ["Registro Evento", "Historial Eventos", "Dashboard"]
        if rol == "TECNICO":
            return ["Registro Evento", "Historial Eventos", "Editar Reportes"]
        if rol == "SUPERVISOR":
            return ["Registro Evento", "Historial Eventos", "Dashboard"]
        return ["Registro Evento", "Historial Eventos"]

    return ["Historial Eventos"]


opciones_menu = _menu_por_usuario()
menu = st.sidebar.radio("Menú", opciones_menu, key="menu_principal_volcan")


if menu == "Registro Evento":
    if empresa == "VOLCAN" or ACCESO_TOTAL:
        registro_ot()
    else:
        st.error("No tienes permisos para registrar eventos VOLCAN.")

elif menu == "Historial Eventos":
    if empresa == "VOLCAN" or ACCESO_TOTAL:
        mostrar_historial_eventos()
    else:
        st.error("No tienes permisos para visualizar eventos VOLCAN.")

elif menu == "Dashboard":
    if ACCESO_TOTAL or (empresa == "VOLCAN" and rol in ["PLANNER", "SUPERVISOR"]):
        mostrar_dashboard()
    else:
        st.error("No tienes permisos para visualizar el Dashboard VOLCAN.")

elif menu == "Registro Trackless":
    if ACCESO_TOTAL:
        registro_trackless()
    else:
        st.error("No tienes permisos para Trackless.")

elif menu == "Dashboard Trackless":
    if ACCESO_TOTAL:
        mostrar_dashboard_trackless()
    else:
        st.error("No tienes permisos para Trackless.")

elif menu == "Registro Lucarbal":
    if ACCESO_TOTAL or (empresa == "LUCARBAL" and rol == "TECNICO"):
        registro_lucarbal()
    else:
        st.error("Solo los técnicos LUCARBAL autorizados pueden registrar eventos.")

elif menu == "Historial Lucarbal":
    if empresa == "LUCARBAL" or ACCESO_TOTAL:
        mostrar_historial_lucarbal()
    else:
        st.error("No tienes permisos para visualizar el Historial LUCARBAL.")

elif menu == "Dashboard Lucarbal":
    if ACCESO_TOTAL or (
        empresa == "LUCARBAL" and rol in ["PLANNER", "SUPERVISOR"]
    ):
        mostrar_dashboard_lucarbal()
    else:
        st.error("No tienes permisos para visualizar el Dashboard LUCARBAL.")

elif menu == "Editar Reportes":
    # Técnicos: el editor filtra sus propios registros y su empresa.
    # Acceso total: administración general de Bombeo y LUCARBAL.
    if ACCESO_TOTAL or (
        rol == "TECNICO" and empresa in ["VOLCAN", "LUCARBAL"]
    ):
        editar_registros()
    else:
        st.error("No tienes permisos para editar reportes.")

elif menu == "Registro Mantto Planta Móvil":
    if ACCESO_TOTAL or (
        empresa == "LIVERH" and rol in ["TECNICO", "PLANNER"]
    ):
        registro_planta_movil()
    else:
        st.error("No tienes permisos para registrar mantenimiento de Planta Móvil.")

elif menu == "Historial Mantto Planta Móvil":
    if ACCESO_TOTAL or (
        empresa == "LIVERH" and rol in ["TECNICO", "SUPERVISOR", "PLANNER"]
    ):
        mostrar_historial_planta_movil()
    else:
        st.error("No tienes permisos para visualizar el historial de Planta Móvil.")

elif menu == "Registro Despacho Mixers":
    if ACCESO_TOTAL or (
        empresa == "LIVERH" and rol in ["SUPERVISOR", "PLANNER"]
    ):
        registro_despacho_mixers()
    else:
        st.error("No tienes permisos para registrar despacho de mixers.")

elif menu == "Historial Despacho Mixers":
    if ACCESO_TOTAL or (
        empresa == "LIVERH" and rol in ["SUPERVISOR", "PLANNER"]
    ):
        mostrar_historial_despacho_mixers()
    else:
        st.error("No tienes permisos para visualizar el historial de despacho de mixers.")
