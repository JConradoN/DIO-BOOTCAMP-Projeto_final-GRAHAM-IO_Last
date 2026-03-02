import os
import json
import pandas as pd
import streamlit as st
import unicodedata
from datetime import datetime
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GRAHAM-IO | Bradesco", page_icon="🏦", layout="wide")

# Configurações de Caminho e Cliente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()

# --- FUNÇÕES CORE (MANTIDAS DO v007) ---

def normalizar_nome(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).strip().lower().replace(" ", "_")

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

def tocar_audio(texto):
    tts = gTTS(text=texto, lang='pt-br')
    tts.save("temp_voice.mp3")
    with open("temp_voice.mp3", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    os.remove("temp_voice.mp3")

# --- INTERFACE STREAMLIT ---

st.title("🏦 GRAHAM-IO: Consultoria de Valor")
st.markdown("---")

# 1. Seleção de Usuário na Sidebar (Muito mais prático que voz para login)
pastas_usuarios = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
usuario_selecionado = st.sidebar.selectbox("Selecione o Cliente", ["Selecione..."] + pastas_usuarios)

if usuario_selecionado != "Selecione...":
    perfil, produtos, saldo = carregar_dados_usuario(usuario_selecionado)
    
    # Sidebar - Infos do Cliente
    st.sidebar.header(f"👤 {perfil['nome']}")
    st.sidebar.metric("Saldo Consolidado", f"R$ {saldo:.2f}")
    st.sidebar.info(f"**Perfil:** {perfil['perfil_investidor']}\n\n**Meta:** {perfil['objetivo_principal']}")
    
    # Inicializar Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"Graham-IO. Cliente: {perfil['nome']}. Saldo: {saldo}. Perfil: {perfil['perfil_investidor']}. Produtos: {json.dumps(produtos)}"}]

    # Exibir histórico de mensagens
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Botão de Voz
    if st.button("🎙️ Falar com Graham-IO"):
        with sr.Microphone() as source:
            st.toast("Ouvindo...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = recognizer.listen(source, timeout=5)
                with open("st_audio.wav", "wb") as f: f.write(audio.get_wav_data())
                with open("st_audio.wav", "rb") as f:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
                
                pergunta = transcript.text
                st.chat_message("user").markdown(pergunta)
                st.session_state.messages.append({"role": "user", "content": pergunta})

                # Gerar Resposta
                with st.chat_message("assistant"):
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages)
                    resposta = response.choices[0].message.content
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                    registrar_log(usuario_selecionado, pergunta, resposta)
                    tocar_audio(resposta)
            except Exception as e:
                st.error(f"Erro ao captar voz: {e}")

else:
    st.info("👈 Por favor, selecione um cliente na barra lateral para iniciar a consultoria.")