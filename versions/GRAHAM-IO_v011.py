import os
import json
import pandas as pd
import streamlit as st
import unicodedata
from datetime import datetime
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import plotly.express as px
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GRAHAM-IO | Bradesco", page_icon="🏦", layout="wide")

# Mantendo sua chave original
client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

# --- FUNÇÕES DE SUPORTE ---

def autoplay_audio(text):
    """Gera áudio e injeta HTML para tocar automaticamente sem player visível"""
    try:
        tts = gTTS(text=text, lang='pt-br')
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
        os.remove("temp.mp3")
    except Exception as e:
        st.error(f"Erro no áudio: {e}")

def get_alocacao(perfil_nome):
    perfis = {
        "Conservador": {"Renda Fixa": 80, "Ações": 10, "Reserva": 10},
        "Moderado": {"Renda Fixa": 50, "Ações": 40, "Reserva": 10},
        "Arrojado": {"Renda Fixa": 25, "Ações": 65, "Reserva": 10}
    }
    return perfis.get(perfil_nome, perfis["Moderado"])

def carregar_dados(pasta):
    try:
        path = os.path.join(DATA_PATH, pasta)
        with open(os.path.join(path, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perf = json.load(f)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            prod = json.load(f)
        df = pd.read_csv(os.path.join(path, 'transacoes.csv'))
        df['v'] = df.apply(lambda x: x['valor'] if str(x['tipo']).lower() == 'entrada' else -x['valor'], axis=1)
        return perf, prod, df['v'].sum()
    except: return None, None, 0

# --- INTERFACE ---
st.title("🏦 GRAHAM-IO: Consultoria Bradesco")

pastas = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
sel = st.sidebar.selectbox("👤 Selecionar Cliente", ["Selecione..."] + pastas)

if sel != "Selecione...":
    perfil, produtos, saldo = carregar_dados(sel)
    
    # Sidebar - Visual da v009 (Métricas + Gráfico)
    st.sidebar.metric("Saldo Líquido", f"R$ {saldo:.2f}")
    aloc = get_alocacao(perfil['perfil_investidor'])
    fig = px.pie(values=list(aloc.values()), names=list(aloc.keys()), hole=0.4,
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=True, height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.sidebar.plotly_chart(fig, use_container_width=True)
    st.sidebar.caption(f"Estratégia: {perfil['perfil_investidor']}")

    # Inicializar Chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar histórico
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Entrada de Dados
    prompt = st.chat_input("Pergunte ao Graham...")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: btn_voz = st.button("🎙️ Voz")

    if btn_voz or prompt:
        pergunta = prompt
        if btn_voz:
            with sr.Microphone() as source:
                st.toast("Ouvindo...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    with open("st_audio.wav", "wb") as f: f.write(audio.get_wav_data())
                    with open("st_audio.wav", "rb") as f:
                        t = client.audio.transcriptions.create(model="whisper-1", file=f)
                    pergunta = t.text
                except: st.error("Não ouvi nada."); pergunta = None

        if pergunta:
            st.session_state.messages.append({"role": "user", "content": pergunta})
            st.chat_message("user").markdown(pergunta)

            # Prompt com limite rigoroso de palavras
            sys = {"role": "system", "content": f"Você é o GRAHAM-IO. Responda em NO MÁXIMO 30 palavras. Seja direto e use Benjamin Graham como base. Saldo: R${saldo:.2f}. Cliente: {perfil['nome']}."}
            
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[sys] + st.session_state.messages)
            resposta = res.choices[0].message.content
            
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            with st.chat_message("assistant"):
                st.markdown(resposta)
                autoplay_audio(resposta) # Toca o som sem mostrar player
            
            # Auditoria
            with open(os.path.join(DATA_PATH, sel, "log_auditoria.txt"), "a") as f:
                f.write(f"[{datetime.now()}] U: {pergunta} | A: {resposta}\n")
            
            st.rerun()
else:
    st.info("Selecione um cliente na barra lateral.")