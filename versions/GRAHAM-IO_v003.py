import os
import json
import pandas as pd
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import playsound

# 1. Configuração de Caminhos e Cliente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

# Substitua pela sua chave real
client = OpenAI(api_key="SUA_CHAVE_AQUI")

def carregar_base_conhecimento():
    """Carrega os dados financeiros da pasta data/"""
    try:
        with open(os.path.join(DATA_PATH, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)
        transacoes = pd.read_csv(os.path.join(DATA_PATH, 'transacoes.csv'))
        saldo_atual = transacoes['valor'].sum()
        return perfil, produtos, saldo_atual
    except Exception as e:
        print(f"\n[ERRO]: Falha ao carregar base de dados: {e}")
        return None, None, 0

# Inicialização global de dados e recognizer
perfil, produtos, saldo = carregar_base_conhecimento()
recognizer = sr.Recognizer()

# Configurações do System Prompt
SYSTEM_PROMPT = f"""
Você é o GRAHAM-IO, consultor sênior do Bradesco e especialista em Benjamin Graham.
CLIENTE: {perfil['nome'] if perfil else 'Cliente'}, Perfil: {perfil['perfil_investidor'] if perfil else 'Moderado'}.
SALDO: R$ {saldo:.2f}. PRODUTOS: {json.dumps(produtos)}.

REGRAS:
1. Respostas extremamente curtas para voz (máximo 4 frases).
2. Foco total em Margem de Segurança e ativos da base.
3. Se o saldo for positivo, sugira aportes conservadores.
"""

historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]
PALAVRAS_SAIDA = ["sair", "tchau", "obrigado", "encerrar", "finalizar", "até logo"]

# 2. Funções de Áudio e Processamento
def falar(texto, nome_arquivo="v_temp.mp3"):
    """Sintetiza voz e reproduz"""
    try:
        print(f"\nGRAHAM-IO: {texto}")
        tts = gTTS(text=texto, lang='pt-br')
        tts.save(nome_arquivo)
        playsound.playsound(nome_arquivo)
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
    except Exception as e:
        print(f"Erro ao reproduzir áudio: {e}")

def ouvir():
    """Captura áudio e transcreve via Whisper"""
    with sr.Microphone() as source:
        print("\n[GRAHAM-IO está ouvindo... fale agora]")
        try:
            # Captura o áudio com limites para não travar
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            with open("t_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            with open("t_audio.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            
            if os.path.exists("t_audio.wav"):
                os.remove("t_audio.wav")
            return transcript.text
        except sr.WaitTimeoutError:
            print("... silêncio detectado ...")
            return None
        except Exception as e:
            print(f"Erro na captura/transcrição: {e}")
            return None

def pensar(entrada_usuario):
    """Gera resposta via GPT-4o-mini"""
    global historico_conversa
    historico_conversa.append({"role": "user", "content": entrada_usuario})
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=historico_conversa,
            temperature=0.5
        )
        resposta = response.choices[0].message.content
        historico_conversa.append({"role": "assistant", "content": resposta})
        return resposta
    except Exception as e:
        return f"Desculpe, tive um problema de conexão: {e}"

# 3. Fluxo Principal
if __name__ == "__main__":
    if not perfil:
        print("Finalizando: Arquivos de dados não encontrados.")
        exit()

    # --- CALIBRAÇÃO ÚNICA DO MICROFONE ---
    with sr.Microphone() as source:
        print("\n[CONFIG] Calibrando microfone para o ruído ambiente... Fique em silêncio.")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        recognizer.dynamic_energy_threshold = True
        print("[CONFIG] Calibração concluída.\n")

    print("="*50)
    print(f"GRAHAM-IO ONLINE | SALDO ATUAL: R$ {saldo:.2f}")
    print("="*50)
    
    # Saudação Inicial
    saudacao = f"Olá {perfil['nome']}, sou o GRAHAM-IO. Temos R$ {saldo:.2f} para investir na sua meta de {perfil['objetivo_principal']}. Como posso ajudar hoje?"
    falar(saudacao)
    
    while True:
        pergunta = ouvir()
        
        if pergunta:
            print(f"VOCÊ: {pergunta}")
            
            # Checar encerramento
            if any(p in pergunta.lower() for p in PALAVRAS_SAIDA):
                falar(f"Até mais, {perfil['nome']}. O Bradesco e o Graham-IO desejam bons investimentos!")
                break
                
            # Processar com GPT
            resposta = pensar(pergunta)
            falar(resposta)
        else:
            # Pequena pausa para não sobrecarregar o processador no loop de silêncio
            print("... aguardando interação ...")