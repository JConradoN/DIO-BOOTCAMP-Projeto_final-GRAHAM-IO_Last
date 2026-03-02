import os
import json
import pandas as pd
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import playsound

# 1. Configuração de Caminhos (Baseado no teu ls -r)
# Como o script e a pasta 'data' estão no mesmo diretório (NOVA-BIA), usamos:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

client = OpenAI(api_key="SUA_CHAVE_AQUI")

def carregar_base_conhecimento():
    """Lê os teus ficheiros de dados para personalizar o atendimento"""
    try:
        with open(os.path.join(DATA_PATH, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            
        transacoes = pd.read_csv(os.path.join(DATA_PATH, 'transacoes.csv'))
        saldo_atual = transacoes['valor'].sum()
        
        return perfil, produtos, saldo_atual
    except Exception as e:
        print(f"\n[ERRO]: Não foi possível carregar os dados em {DATA_PATH}")
        print(f"Detalhe: {e}")
        return None, None, 0

# Inicialização dos dados do João Silva
perfil, produtos, saldo = carregar_base_conhecimento()

if not perfil:
    print("Erro crítico: Base de dados não encontrada. Verifica a pasta 'data'.")
    exit()

# 2. Persona e Regras do Sistema
SYSTEM_PROMPT = f"""
És o GRAHAM-IO, consultor sénior do Bradesco e especialista em Benjamin Graham.
DADOS DO CLIENTE: Nome: {perfil['nome']}, Perfil: {perfil['perfil_investidor']}, Saldo: R$ {saldo:.2f}.
BASE DE PRODUTOS: {json.dumps(produtos)}

REGRAS:
1. Começa com uma saudação personalizada e menciona o saldo.
2. Segue a filosofia de Benjamin Graham (Margem de Segurança).
3. Respostas curtas e diretas (máximo 5 frases).
4. Se o produto não estiver na base ou for de risco elevado, recusa por segurança.
"""

historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]
PALAVRAS_SAIDA = ["sair", "tchau", "obrigado", "encerrar", "finalizar"]

# 3. Funções de Áudio (Robustas como a BIA original)
def falar(texto, nome_arquivo="temp_voz.mp3"):
    try:
        print(f"\nGRAHAM-IO: {texto}")
        tts = gTTS(text=texto, lang='pt-br')
        tts.save(nome_arquivo)
        playsound.playsound(nome_arquivo)
        os.remove(nome_arquivo)
    except Exception as e:
        print(f"Erro de áudio: {e}")

def ouvir():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True 
    with sr.Microphone() as source:
        print("\n[GRAHAM-IO está a ouvir...]")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=10)
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            with open("temp.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            os.remove("temp.wav")
            return transcript.text
        except:
            return None

def pensar(entrada_usuario):
    global historico_conversa
    historico_conversa.append({"role": "user", "content": entrada_usuario})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico_conversa,
        temperature=0.5
    )
    resposta = response.choices[0].message.content
    historico_conversa.append({"role": "assistant", "content": resposta})
    return resposta

# --- Execução Principal ---
if __name__ == "__main__":
    print("="*50)
    print(f"GRAHAM-IO LIGADO | CLIENTE: {perfil['nome'].upper()}")
    print("="*50)
    
    # Saudação Proativa Inicial
    saudacao_inicial = f"Olá {perfil['nome']}, sou o GRAHAM-IO. Notei que tens R$ {saldo:.2f} disponíveis. Como posso ajudar com a tua meta de {perfil['objetivo_principal']} hoje?"
    falar(saudacao_inicial)
    
    while True:
        pergunta = ouvir()
        if pergunta:
            print(f"TU: {pergunta}")
            
            if any(p in pergunta.lower() for p in PALAVRAS_SAIDA):
                falar(f"Até breve, {perfil['nome']}. Investe com segurança!")
                break
                
            resposta = pensar(pergunta)
            falar(resposta)
        else:
            print("... (A aguardar voz)")