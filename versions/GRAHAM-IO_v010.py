import os
import json
import pandas as pd
import streamlit as st
import unicodedata
from datetime import datetime
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GRAHAM-IO | Bradesco", page_icon="🏦", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()

# --- FUNÇÕES CORE ---

def carregar_dados_usuario(nome_pasta):
    try:
        caminho_base = os.path.join(DATA_PATH, nome_pasta)
        with open(os.path.join(caminho_base, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)
        transacoes = pd.read_csv(os.path.join(caminho_base, 'transacoes.csv'))
        transacoes['valor_calc'] = transacoes.apply(lambda x: x['valor'] if str(x['tipo']).lower() == 'entrada' else -x['valor'], axis=1)
        return perfil, produtos, transacoes['valor_calc'].sum()
    except: return None, None, 0

def registrar_log(pasta_nome, msg_user, res_ai):
    caminho_log = os.path.join(DATA_PATH, pasta_nome, "log_auditoria.txt")
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(caminho_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] USER: {msg_user} | AI: {res_ai}\n")

# --- INTERFACE ---
st.title("🏦 GRAHAM-IO")

pastas_usuarios = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
usuario_selecionado = st.sidebar.selectbox("👤 Selecionar Cliente", ["Selecione..."] + pastas_usuarios)

if usuario_selecionado != "Selecione...":
    perfil, produtos, saldo = carregar_dados_usuario(usuario_selecionado)
    st.sidebar.metric("Saldo Real", f"R$ {saldo:.2f}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    prompt = st.chat_input("Dúvida financeira...")
    btn_voz = st.button("🎙️ Falar")

    if btn_voz or prompt:
        pergunta = prompt
        if btn_voz:
            with sr.Microphone() as source:
                st.toast("Ouvindo...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    with open("st_audio.wav", "wb") as f: f.write(audio.get_wav_data())
                    with open("st_audio.wav", "rb") as f:
                        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
                    pergunta = transcript.text
                except: pergunta = None

        if pergunta:
            st.session_state.messages.append({"role": "user", "content": pergunta})
            st.chat_message("user").markdown(pergunta)

            # --- PROMPT REFORÇADO (PARA EVITAR VERBOSIDADE) ---
            sys_msg = {
                "role": "system", 
                "content": f"""Você é o GRAHAM-IO. Seja EXTREMAMENTE breve (máximo 2 parágrafos).
                Vá direto ao ponto. Use a filosofia de Benjamin Graham.
                Cliente: {perfil['nome']}, Perfil: {perfil['perfil_investidor']}, Saldo: R${saldo:.2f}.
                Produtos: {json.dumps(produtos)}.
                Sempre comece citando o saldo se for relevante."""
            }
            
            # Enviamos o sistema SEMPRE no topo para garantir obediência
            full_messages = [sys_msg] + st.session_state.messages
            
            response = client.chat.completions.create(model="gpt-4o-mini", messages=full_messages)
            resposta = response.choices[0].message.content
            
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            with st.chat_message("assistant"):
                st.markdown(resposta)
                
                # --- CORREÇÃO DO ÁUDIO (Componente Nativo) ---
                tts = gTTS(text=resposta, lang='pt-br')
                tts.save("resp.mp3")
                st.audio("resp.mp3", format="audio/mp3", autoplay=True)
            
            registrar_log(usuario_selecionado, pergunta, resposta)