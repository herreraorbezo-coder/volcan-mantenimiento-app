# ==========================================================
# STYLES.PY
# ESTILOS VISUALES - VOLCAN APP
# ==========================================================

import streamlit as st
import base64
import os


def cargar_imagen_base64(ruta):

    if not os.path.exists(ruta):
        return None

    with open(ruta, "rb") as img:
        return base64.b64encode(img.read()).decode()


def aplicar_estilos_globales():

    st.markdown(
        """
        <style>

        .stApp {
            background: linear-gradient(135deg, #0f0f0f 0%, #1c1c1c 45%, #2b2b2b 100%);
            color: #ffffff;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111111 0%, #2b2b2b 100%);
            border-right: 2px solid #b71c1c;
        }

        section[data-testid="stSidebar"] * {
            color: #ffffff;
        }

        .main-title {
            font-size: 42px;
            font-weight: 900;
            text-align: center;
            color: #ffffff;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }

        .main-subtitle {
            font-size: 18px;
            text-align: center;
            color: #d6d6d6;
            margin-bottom: 25px;
        }

        .login-card {
            max-width: 620px;
            margin: 50px auto;
            padding: 42px 48px;
            border-radius: 24px;
            background: rgba(15, 15, 15, 0.88);
            box-shadow: 0px 25px 70px rgba(0, 0, 0, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .login-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 16px;
        }

        .login-line {
            width: 90px;
            height: 4px;
            background: #d32f2f;
            border-radius: 10px;
            margin: 18px auto 25px auto;
        }

        .feature-box {
            background: rgba(255, 255, 255, 0.06);
            border-left: 4px solid #d32f2f;
            padding: 14px 18px;
            border-radius: 12px;
            margin-top: 18px;
            color: #e0e0e0;
            font-size: 14px;
        }

        .footer-text {
            text-align: center;
            color: #9e9e9e;
            font-size: 12px;
            margin-top: 28px;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.06);
            padding: 18px;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0px 8px 25px rgba(0,0,0,0.25);
        }

        div[data-testid="stMetricValue"] {
            color: #ffffff;
            font-size: 28px;
            font-weight: 800;
        }

        div[data-testid="stMetricLabel"] {
            color: #d0d0d0;
            font-weight: 600;
        }

        .stButton > button {
            background: linear-gradient(90deg, #b71c1c, #d32f2f);
            color: white;
            border-radius: 12px;
            border: none;
            font-weight: 700;
            padding: 0.6rem 1rem;
        }

        .stButton > button:hover {
            background: linear-gradient(90deg, #d32f2f, #ef5350);
            color: white;
            border: none;
        }

        .stTextInput input, .stTextArea textarea {
            border-radius: 10px;
        }

        .stSelectbox div {
            border-radius: 10px;
        }

        h1, h2, h3 {
            color: #ffffff;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def fondo_login(ruta_fondo="assets/fondo_mina.jpg"):

    img_base64 = cargar_imagen_base64(ruta_fondo)

    if img_base64 is None:
        return

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(0,0,0,0.68), rgba(0,0,0,0.82)),
                url("data:image/jpg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def mostrar_logo(ruta_logo="assets/logo_volcan.png", ancho=180):

    if os.path.exists(ruta_logo):
        st.image(ruta_logo, width=ancho)
    else:
        st.markdown("### VOLCAN")