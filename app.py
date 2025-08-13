import json
import streamlit as st
import requests
import base64

# URL de tu Lambda (API Gateway)
LAMBDA_URL = "https://9sbmriwy50.execute-api.us-east-1.amazonaws.com/default/EvaFrecuente"

st.set_page_config(page_title="Texto ↔ Audio", layout="wide", initial_sidebar_state="collapsed")

# --- Estilos CSS ---
st.markdown("""
    <style>
    .stApp {background-color: #f9f9fb;}
    .stButton>button {
        background-color: #4CAF50; color: white; padding: 10px 24px;
        border-radius: 8px; border: none; cursor: pointer; font-size: 16px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {background-color: #45a049; transform: scale(1.02);}
    .stRadio>label {font-size: 1.1em; font-weight: bold;}
    .stTextArea, .stFileUploader {margin-top: 15px; margin-bottom: 15px;}
    .result-box {background-color:#e6ffe6; padding:15px; border-radius:10px; border-left: 5px solid #4CAF50;}
    .audio-box {background-color:#e6f0ff; padding:15px; border-radius:10px; border-left: 5px solid #2196F3;}
    </style>
""", unsafe_allow_html=True)

# --- Título ---
st.title("🗣️ Texto ↔ Audio con AWS Lambda")
st.markdown("Convierte texto a voz o voz a texto usando Amazon Polly y Transcribe.")

# --- Selección de entrada ---
option = st.radio("Elige el tipo de entrada:", ["Texto", "Audio"])

text_input = ""
audio_bytes = None

if option == "Texto":
    text_input = st.text_area("✍️ Escribe tu texto aquí para convertirlo a audio:", height=150, placeholder="Escribe 'Hola mundo' o cualquier frase...")
elif option == "Audio":
    uploaded_file = st.file_uploader("🎤 Sube tu archivo de audio (MP3 o WAV):", type=["mp3","wav"])
    if uploaded_file:
        audio_bytes = uploaded_file.read()
        st.audio(audio_bytes, format=f"audio/{uploaded_file.type.split('/')[-1]}")

# --- Botón de procesamiento ---
if st.button("🚀 Procesar"):
    payload = None
    if option == "Texto" and text_input.strip() != "":
        payload = {"text": text_input}
    elif option == "Audio" and audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {"audio_base64": audio_b64}
    else:
        st.warning("⚠️ Debes escribir texto o subir un archivo de audio para procesar.")
        st.stop()

    result = {}
    # --- Spinner mientras llega la respuesta ---
    with st.spinner("⏳ Procesando... Esto puede tardar unos segundos para audios largos."):
        try:
            response = requests.post(LAMBDA_URL, json=payload, timeout=300)
            if response.status_code == 200:
                result = response.json()
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", error_data.get("message", f"Error desconocido (Código {response.status_code})"))
                except json.JSONDecodeError:
                    error_message = f"Error del servidor (Código {response.status_code}): No se pudo decodificar la respuesta JSON."
                st.error(f"❌ Error del servidor: {error_message}")
                st.stop()
        except requests.exceptions.Timeout:
            st.error("⏳ La solicitud ha excedido el tiempo de espera.")
            st.stop()
        except requests.exceptions.ConnectionError:
            st.error("🔌 Error de conexión. Revisa la URL de Lambda y tu red.")
            st.stop()
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error general: {e}")
            st.stop()

    # --- Mostrar resultados en dos columnas ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Texto Resultante")
        if "text" in result:
            st.markdown(f"<div class='result-box'>{result['text']}</div>", unsafe_allow_html=True)
        elif option == "Audio":
            if "error" in result:
                st.error(result["error"])
            else:
                st.info("La transcripción no generó texto o aún está en proceso.")
        else:
            st.info("No hay texto para mostrar (procesaste de texto a audio).")

    with col2:
        st.subheader("🔊 Audio Resultante")
        if "audio_base64" in result:
            try:
                audio_out = base64.b64decode(result["audio_base64"])
                st.audio(audio_out, format="audio/mp3")
            except Exception as e:
                st.error(f"❌ No se pudo reproducir el audio: {e}")
        elif option == "Texto":
            if "error" in result:
                st.error(result["error"])
            else:
                st.info("El audio no fue generado o está en proceso.")
        else:
            st.info("No hay audio para mostrar (procesaste de audio a texto).")
