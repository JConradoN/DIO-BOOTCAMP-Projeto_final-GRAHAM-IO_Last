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
client = OpenAI(api_key="SUA_CHAVE_AQUI")
recognizer = sr.Recognizer()

def carregar_dados_usuario(nome_dito):
    """Identifica a pasta do usuário e processa saldo e perfil"""
    try:
        # Normaliza o nome para buscar a pasta (ex: "João Silva" -> "joao_silva")
        pasta_usuario = nome_dito.lower().strip().replace(" ", "_")
        caminho_base = os.path.join(DATA_PATH, pasta_usuario)
        
        if not os.path.exists(caminho_base):
            return None, None, 0

        # 1. Carregar Perfil
        with open(os.path.join(caminho_base, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        
        # 2. Carregar Produtos (Geral da pasta data)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            
        # 3. Cálculo de Saldo Corrigido (Entradas vs Saídas)
        transacoes = pd.read_csv(os.path.join(caminho_base, 'transacoes.csv'))
        transacoes['valor_final'] = transacoes.apply(
            lambda x: x['valor'] if x['tipo'].lower() == 'entrada' else -x['valor'], axis=1
        )
        saldo_atual = transacoes['valor_final'].sum()
        
        return perfil, produtos, saldo_atual
    except Exception as e:
        print(f"\n[ERRO]: Falha ao processar dados: {e}")
        return None, None, 0

# 2. Funções de Áudio
def falar(texto, nome_arquivo="v_temp.mp3"):
    try:
        print(f"\nGRAHAM-IO: {texto}")
        tts = gTTS(text=texto, lang='pt-br')
        tts.save(nome_arquivo)
        playsound.playsound(nome_arquivo)
        if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
    except Exception as e: print(f"Erro áudio: {e}")

def ouvir(timeout=5):
    with sr.Microphone() as source:
        print(f"\n[GRAHAM-IO ouvindo...]")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            with open("t_audio.wav", "wb") as f: f.write(audio.get_wav_data())
            with open("t_audio.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            if os.path.exists("t_audio.wav"): os.remove("t_audio.wav")
            return transcript.text
        except: return None

def pensar(entrada_usuario, contexto_prompt):
    global historico_conversa
    historico_conversa.append({"role": "user", "content": entrada_usuario})
    response = client.chat.completions.create(model="gpt-4o-mini", messages=historico_conversa, temperature=0.5)
    resposta = response.choices[0].message.content
    historico_conversa.append({"role": "assistant", "content": resposta})
    return resposta

# 3. Fluxo Principal
if __name__ == "__main__":
    # Calibração Inicial
    with sr.Microphone() as source:
        print("Calibrando microfone...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)

    falar("Olá, sou o GRAHAM-IO. Diga seu nome completo para acessarmos sua conta.")
    nome_usuario = ouvir(timeout=8)

    if nome_usuario:
        print(f"Buscando perfil para: {nome_usuario}")
        perfil, produtos, saldo = carregar_dados_usuario(nome_usuario)

        if perfil:
            # Monta o prompt com os dados do usuário específico
            SYSTEM_PROMPT = f"""
            Você é o GRAHAM-IO, consultor do Bradesco. 
            CLIENTE: {perfil['nome']} | PERFIL: {perfil['perfil_investidor']}
            SALDO REAL: R$ {saldo:.2f} | PRODUTOS: {json.dumps(produtos)}
            REGRAS: Máximo 4 frases. Siga Benjamin Graham. Mencione o saldo no início.
            """
            historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]
            PALAVRAS_SAIDA = ["sair", "tchau", "obrigado", "encerrar"]

            falar(f"Acesso concedido. {perfil['nome']}, seu saldo atual é de {saldo:.2f} reais. Como posso ajudar seu perfil {perfil['perfil_investidor']} hoje?")

            while True:
                pergunta = ouvir()
                if pergunta:
                    print(f"VOCÊ: {pergunta}")
                    if any(p in pergunta.lower() for p in PALAVRAS_SAIDA):
                        falar("Até logo! Invista com segurança.")
                        break
                    falar(pensar(pergunta, SYSTEM_PROMPT))
        else:
            falar("Lamento, não encontrei um perfil com esse nome. Verifique as pastas de dados.")
    else:
        falar("Não consegui ouvir o nome. Reinicie o sistema, por favor.")