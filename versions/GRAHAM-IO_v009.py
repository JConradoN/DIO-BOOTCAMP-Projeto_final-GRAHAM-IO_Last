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
import plotly.express as px  # Nova dependência: pip install plotly

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="GRAHAM-IO | Bradesco", page_icon="🏦", layout="wide")

# Configurações de Caminho e Cliente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
client = OpenAI(api_key="SUA_CHAVE_AQUI")  # Substitua pela sua chave real
recognizer = sr.Recognizer()

# --- FUNÇÕES CORE ---

def get_alocacao_sugerida(perfil_nome):
    """Retorna a distribuição de ativos baseada no perfil de Graham"""
    perfis = {
        "Conservador": {"Renda Fixa": 80, "Ações (Valor)": 10, "Reserva": 10},
        "Moderado": {"Renda Fixa": 50, "Ações (Valor)": 40, "Reserva": 10},
        "Arrojado": {"Renda Fixa": 25, "Ações (Valor)": 65, "Reserva": 10}
    }
    return perfis.get(perfil_nome, perfis["Moderado"])

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
    try:
        tts = gTTS(text=texto, lang='pt-br')
        tts.save("temp_voice.mp3")
        with open("temp_voice.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
            st.markdown(md, unsafe_allow_html=True)
        os.remove("temp_voice.mp3")
    except: pass

# --- INTERFACE ---

st.title("🏦 GRAHAM-IO: Inteligência Patrimonial")
st.caption("Consultoria baseada em Margem de Segurança e Valor Intrínseco")

pastas_usuarios = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
usuario_selecionado = st.sidebar.selectbox("👤 Selecionar Cliente", ["Selecione..."] + pastas_usuarios)

if usuario_selecionado != "Selecione...":
    perfil, produtos, saldo = carregar_dados_usuario(usuario_selecionado)
    
    # --- SIDEBAR COM GRÁFICO ---
    st.sidebar.header(f"Cliente: {perfil['nome']}")
    st.sidebar.metric("Saldo Real", f"R$ {saldo:.2f}")
    
    # Gerar Gráfico de Alocação
    alocacao = get_alocacao_sugerida(perfil['perfil_investidor'])
    df_pizza = pd.DataFrame(list(alocacao.items()), columns=['Classe', 'Percentual'])
    
    fig = px.pie(df_pizza, values='Percentual', names='Classe', 
                 title=f"Sugestão: {perfil['perfil_investidor']}",
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0), height=200)
    
    st.sidebar.plotly_chart(fig, use_container_width=True)
    st.sidebar.divider()
    st.sidebar.info(f"**Objetivo:** {perfil['objetivo_principal']}")

    # --- CHAT INTERFACE ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Container para mensagens
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Entrada de Voz / Texto
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        btn_voz = st.button("🎙️ Ouvir")
    
    prompt = st.chat_input("Ou digite sua dúvida financeira...")

    if btn_voz or prompt:
        pergunta = prompt
        
        if btn_voz:
            with sr.Microphone() as source:
                st.toast("Ouvindo seu comando...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    with open("st_audio.wav", "wb") as f: f.write(audio.get_wav_data())
                    with open("st_audio.wav", "rb") as f:
                        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
                    pergunta = transcript.text
                except:
                    st.warning("Não consegui captar o áudio.")
                    pergunta = None

        if pergunta:
            st.session_state.messages.append({"role": "user", "content": pergunta})
            with chat_container:
                st.chat_message("user").markdown(pergunta)

            # Resposta da IA com contexto
            ctx = [{"role": "system", "content": f"Graham-IO. Cliente: {perfil['nome']}. Saldo: {saldo}. Perfil: {perfil['perfil_investidor']}. Alocação Sugerida: {alocacao}. Produtos Disponíveis: {json.dumps(produtos)}"}]
            full_messages = ctx + st.session_state.messages
            
            response = client.chat.completions.create(model="gpt-4o-mini", messages=full_messages)
            resposta = response.choices[0].message.content
            
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            with chat_container:
                st.chat_message("assistant").markdown(resposta)
            
            registrar_log(usuario_selecionado, pergunta, resposta)
            tocar_audio(resposta)
            st.rerun()

else:
    st.write("### 👋 Bem-vindo ao GRAHAM-IO")
    st.write("Selecione um cliente na barra lateral para carregar o portfólio e iniciar a análise.")