import os
import json
import pandas as pd
import streamlit as st
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import plotly.express as px
import base64
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GRAHAM-IO | Bradesco", page_icon="🏦", layout="wide")

client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

# --- FUNÇÕES DE SUPORTE ---

def play_audio(text):
    """Injeta áudio Base64 para evitar interrupções do Streamlit"""
    try:
        tts = gTTS(text=text, lang='pt-br')
        tts.save("temp_voice.mp3")
        with open("temp_voice.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
        audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        st.components.v1.html(audio_html, height=0)
    except: pass

def obter_prompt_mestre(perfil, produtos, saldo):
    """Lê o arquivo TXT e injeta as variáveis dinâmicas"""
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            template = f.read()
        return template.format(
            nome=perfil['nome'],
            perfil=perfil['perfil_investidor'],
            saldo=saldo,
            objetivo=perfil['objetivo_principal'],
            produtos_json=json.dumps(produtos, indent=2, ensure_ascii=False)
        )
    except: return "Responda de forma breve."

def carregar_dados_usuario(pasta):
    path = os.path.join(DATA_PATH, pasta)
    with open(os.path.join(path, 'perfil_investidor.json'), 'r', encoding='utf-8') as f: p = json.load(f)
    with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f: pr = json.load(f)
    df = pd.read_csv(os.path.join(path, 'transacoes.csv'))
    df['tipo'] = df['tipo'].astype(str).str.lower()
    saldo = df.apply(lambda x: x['valor'] if x['tipo'] == 'entrada' else -x['valor'], axis=1).sum()
    return p, pr, saldo

# --- INTERFACE ---
st.title("🏦 GRAHAM-IO: Inteligência Patrimonial")

pastas = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
selecionado = st.sidebar.selectbox("👤 Selecionar Cliente", ["Selecione..."] + pastas)

if selecionado != "Selecione...":
    # Gerenciamento de Estado de Sessão
    if "current_user" not in st.session_state or st.session_state.current_user != selecionado:
        p, pr, s = carregar_dados_usuario(selecionado)
        st.session_state.perfil, st.session_state.produtos, st.session_state.saldo = p, pr, s
        st.session_state.current_user = selecionado
        st.session_state.messages = []

    # Sidebar Visual
    st.sidebar.metric("Saldo Real", f"R$ {st.session_state.saldo:.2f}")
    aloc_map = {"Conservador": [80, 10, 10], "Moderado": [50, 40, 10], "Arrojado": [25, 65, 10]}
    vals = aloc_map.get(st.session_state.perfil['perfil_investidor'], [50, 40, 10])
    fig = px.pie(values=vals, names=["Renda Fixa", "Ações", "Reserva"], hole=0.4)
    fig.update_layout(showlegend=False, height=200, margin=dict(t=20, b=0, l=0, r=0))
    st.sidebar.plotly_chart(fig, use_container_width=True)

    # Chat History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Inputs
    user_input = st.chat_input("Pergunte ao Graham...")
    if st.button("🎙️ Falar"):
        with sr.Microphone() as source:
            st.toast("Ouvindo...")
            try:
                audio = recognizer.listen(source, timeout=5)
                with open("voice.wav", "wb") as f: f.write(audio.get_wav_data())
                with open("voice.wav", "rb") as f:
                    t = client.audio.transcriptions.create(model="whisper-1", file=f)
                user_input = t.text
            except: st.error("Erro na captura.")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        # Montagem do Contexto com Prompt Externo
        sys_prompt = obter_prompt_mestre(st.session_state.perfil, st.session_state.produtos, st.session_state.saldo)
        full_msgs = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
        
        res = client.chat.completions.create(model="gpt-4o-mini", messages=full_msgs, temperature=0.3)
        resposta = res.choices[0].message.content
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)
            play_audio(resposta)
        
        # Log
        with open(os.path.join(DATA_PATH, selecionado, "log_auditoria.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] U: {user_input} | A: {resposta}\n")

else:
    st.info("Selecione um cliente para iniciar.")