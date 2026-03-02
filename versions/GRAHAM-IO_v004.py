import os
import json
import pandas as pd
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import playsound

# 1. Configurações Iniciais
client = OpenAI(api_key="SUA_CHAVE_AQUI")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
recognizer = sr.Recognizer()

# 2. Funções de Suporte (Áudio e Identificação)
def falar(texto):
    print(f"\nGRAHAM-IO: {texto}")
    tts = gTTS(text=texto, lang='pt-br')
    arquivo = "temp_voz.mp3"
    tts.save(arquivo)
    playsound.playsound(arquivo)
    os.remove(arquivo)

def ouvir():
    with sr.Microphone() as source:
        print("\n[Ouvindo...]")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            with open("temp.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            os.remove("temp.wav")
            return transcript.text
        except:
            return None

# 3. Lógica de Gestão de Usuários e Dados
def carregar_dados_usuario(nome_usuario):
    """
    Busca a pasta do usuário e processa saldo (Entradas - Saídas)
    """
    # Normaliza o nome para buscar a pasta (ex: "João Silva" -> "joao_silva")
    pasta_busca = nome_usuario.lower().replace(" ", "_")
    caminho_usuario = os.path.join(DATA_PATH, pasta_busca)
    
    if not os.path.exists(caminho_usuario):
        return None, 0, None

    try:
        # Carregar Perfil
        with open(os.path.join(caminho_usuario, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        
        # Carregar Produtos (Geral ou específico da pasta se houver)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)

        # Processar Transações com Lógica de Entrada/Saída
        df = pd.read_csv(os.path.join(caminho_usuario, 'transacoes.csv'))
        
        # CORREÇÃO: Aplicar sinal negativo para saídas
        df['valor_ajustado'] = df.apply(
            lambda x: x['valor'] if x['tipo'].lower() == 'entrada' else -x['valor'], axis=1
        )
        saldo_real = df['valor_ajustado'].sum()
        
        return perfil, saldo_real, produtos
    except Exception as e:
        print(f"Erro ao processar dados de {nome_usuario}: {e}")
        return None, 0, None

# 4. Loop de Inteligência
def iniciar_consultoria(perfil, saldo, produtos):
    prompt_sistema = f"""
    Você é o GRAHAM-IO, consultor do Bradesco.
    CLIENTE: {perfil['nome']} | PERFIL: {perfil['perfil_investidor']} | SALDO: R$ {saldo:.2f}
    PRODUTOS: {json.dumps(produtos)}
    
    REGRAS:
    1. Mencione o saldo corrigido e o perfil logo no início.
    2. Se o saldo for baixo, priorize economia. Se for alto, sugira os produtos da base.
    3. Use a filosofia de Benjamin Graham (Segurança em primeiro lugar).
    """
    
    historico = [{"role": "system", "content": prompt_sistema}]
    falar(f"Acesso concedido. Olá {perfil['nome']}, identifiquei seu perfil {perfil['perfil_investidor']}. Seu saldo consolidado é de {saldo:.2f} reais. Como posso ajudar?")

    while True:
        pergunta = ouvir()
        if pergunta:
            print(f"VOCÊ: {pergunta}")
            if any(p in pergunta.lower() for p in ["sair", "encerrar", "obrigado"]):
                falar("Encerrando consultoria. O Bradesco e Graham desejam um ótimo dia!")
                break
            
            historico.append({"role": "user", "content": pergunta})
            response = client.chat.completions.create(model="gpt-4o-mini", messages=historico)
            resposta = response.choices[0].message.content
            historico.append({"role": "assistant", "content": resposta})
            falar(resposta)

# 5. Fluxo Principal (O Portal de Entrada)
if __name__ == "__main__":
    # Calibração inicial do silêncio
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print("=== SISTEMA GRAHAM-IO: RECONHECIMENTO DE USUÁRIO ===")
    falar("Olá, sou o GRAHAM-IO. Para iniciarmos sua consultoria segura, por favor, diga seu nome completo.")
    
    nome_dito = ouvir()
    
    if nome_dito:
        print(f"Identificando: {nome_dito}")
        perfil, saldo, produtos = carregar_dados_usuario(nome_dito)
        
        if perfil:
            iniciar_consultoria(perfil, saldo, produtos)
        else:
            falar(f"Lamento, mas não encontrei uma pasta de dados para o nome {nome_dito}. Verifique se a pasta existe em {DATA_PATH}.")
    else:
        falar("Não consegui ouvir seu nome. Por favor, reinicie o sistema.")