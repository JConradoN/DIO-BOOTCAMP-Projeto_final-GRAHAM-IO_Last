import os
import json
import pandas as pd
import streamlit as st
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import plotly.express as px
import base64
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GRAHAM-IO", page_icon="🏦", layout="wide")

client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# --- NOVA FUNÇÃO DE ÁUDIO SEM INTERRUPÇÃO ---
def play_audio_final(text):
    """Injeta o áudio de forma que o Streamlit não o interrompa"""
    try:
        tts = gTTS(text=text, lang='pt-br')
        # Usamos um nome fixo para evitar acúmulo de arquivos, 
        # o timestamp no HTML resolve o cache.
        filename = "speech.mp3" 
        tts.save(filename)
        
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
        # O segredo: Injetar o HTML e NÃO dar rerun imediatamente
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        st.components.v1.html(audio_html, height=0)
    except Exception as e:
        st.error(f"Erro: {e}")

# --- DADOS ---
def carregar_tudo(pasta):
    path = os.path.join(DATA_PATH, pasta)
    with open(os.path.join(path, 'perfil_investidor.json'), 'r', encoding='utf-8') as f: p = json.load(f)
    with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f: pr = json.load(f)
    df = pd.read_csv(os.path.join(path, 'transacoes.csv'))
    saldo = df.apply(lambda x: x['valor'] if x['tipo'].lower() == 'entrada' else -x['valor'], axis=1).sum()
    return p, pr, saldo

# --- INTERFACE ---
st.title("🏦 GRAHAM-IO")

pastas = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
sel = st.sidebar.selectbox("👤 Cliente", ["Selecione..."] + pastas)

if sel != "Selecione...":
    perfil, produtos, saldo = carregar_tudo(sel)
    st.sidebar.metric("Saldo Líquido", f"R$ {saldo:.2f}")
    
    # Gráfico (v009)
    mapa = {"Conservador": [80, 10, 10], "Moderado": [50, 40, 10], "Arrojado": [25, 65, 10]}
    vals = mapa.get(perfil['perfil_investidor'], [50, 40, 10])
    df_p = pd.DataFrame({"Classe": ["Renda Fixa", "Ações", "Reserva"], "Perc": vals})
    fig = px.pie(df_p, values='Perc', names='Classe', hole=0.4)
    fig.update_layout(showlegend=False, height=200, margin=dict(t=0, b=0, l=0, r=0))
    st.sidebar.plotly_chart(fig, use_container_width=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat historico
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Captura de input
    prompt = st.chat_input("Fale com o Graham...")
    if st.button("🎙️ Acionar Microfone"):
        with sr.Microphone() as source:
            st.toast("Ouvindo...")
            try:
                audio = recognizer.listen(source, timeout=5)
                with open("voice.wav", "wb") as f: f.write(audio.get_wav_data())
                with open("voice.wav", "rb") as f:
                    t = client.audio.transcriptions.create(model="whisper-1", file=f)
                prompt = t.text
            except: st.error("Falha na captura.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # Resposta Curta
        sys = {"role": "system", "content": f"Você é o GRAHAM-IO. Seja muito direto (máximo 20 palavras). Saldo: {saldo}."}
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[sys] + st.session_state.messages)
        resposta = res.choices[0].message.content
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)
            play_audio_final(resposta) # Toca sem interromper
        
        # Log de Auditoria
        with open(os.path.join(DATA_PATH, sel, "log_auditoria.txt"), "a") as f:
            f.write(f"[{datetime.now()}] U: {prompt} | A: {resposta}\n")