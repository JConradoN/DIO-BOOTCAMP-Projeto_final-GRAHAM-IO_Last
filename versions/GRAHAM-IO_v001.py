import os
import json
import pandas as pd
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import playsound
import time

# 1. Configuração e Carregamento de Dados
client = OpenAI(api_key="SUA_CHAVE_AQUI")

def carregar_base_conhecimento():
    """Carrega os arquivos de dados para contextualizar o agente"""
    try:
        with open('data/perfil_investidor.json', 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        
        with open('data/produtos_financeiros.json', 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            
        transacoes = pd.read_csv('data/transacoes.csv')
        saldo_atual = transacoes['valor'].sum() # Simulação simples de saldo
        
        return perfil, produtos, saldo_atual
    except Exception as e:
        print(f"Erro ao carregar base de dados: {e}")
        return None, None, 0

# Carrega os dados uma única vez no início
perfil, produtos, saldo = carregar_base_conhecimento()

# 2. Construção do Contexto Dinâmico
SYSTEM_PROMPT = f"""
Você é o GRAHAM-IO, consultor sênior de investimentos do Bradesco/Ágora.
Você deve basear suas respostas nos seguintes dados reais:

CLIENTE: {perfil['nome']}
PERFIL: {perfil['perfil_investidor']}
META: {perfil['objetivo_principal']}
SALDO EM CONTA: R$ {saldo:.2f}

PRODUTOS DISPONÍVEIS: {json.dumps(produtos)}

REGRAS:
1. Use a filosofia de Benjamin Graham (Margem de Segurança).
2. Se o saldo for positivo, sugira aportes nos produtos da base.
3. Respostas curtas (máximo 5 frases) para voz.
4. Se o usuário pedir algo fora da base, diga que não possui dados seguros no momento.
"""

PALAVRAS_SAIDA = ["sair", "encerrar", "tchau", "obrigado", "finalizar"]
historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]

# 3. Funções de Áudio e IA
def falar(texto):
    print(f"\nGRAHAM-IO: {texto}")
    tts = gTTS(text=texto, lang='pt-br')
    arquivo = "temp_voz.mp3"
    tts.save(arquivo)
    playsound.playsound(arquivo)
    os.remove(arquivo)

def ouvir():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n>>> GRAHAM-IO ouvindo...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            with open("mic_input.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            with open("mic_input.wav", "rb") as audio_file:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            return transcript.text
        except:
            return None

def pensar(texto_usuario):
    historico_conversa.append({"role": "user", "content": texto_usuario})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico_conversa,
        temperature=0.5,
        max_tokens=300
    )
    resposta = response.choices[0].message.content
    historico_conversa.append({"role": "assistant", "content": resposta})
    return resposta

# 4. Loop Principal
if __name__ == "__main__":
    print(f"--- GRAHAM-IO INICIADO (Cliente: {perfil['nome']}) ---")
    
    # Saudação Proativa
    boas_vindas = f"Olá {perfil['nome']}, sou o GRAHAM-IO. Notei que seu perfil é {perfil['perfil_investidor']} e temos um saldo de {saldo} reais para planejar sua meta de {perfil['objetivo_principal']}. Como posso te ajudar hoje?"
    falar(boas_vindas)

    while True:
        pergunta = ouvir()
        if pergunta:
            print(f"VOCÊ: {pergunta}")
            
            if any(p in pergunta.lower() for p in PALAVRAS_SAIDA):
                falar(f"Entendido, {perfil['nome']}. O Bradesco agradece. Lembre-se: preço é o que você paga, valor é o que você leva. Até logo!")
                break
                
            resposta = pensar(pergunta)
            falar(resposta)