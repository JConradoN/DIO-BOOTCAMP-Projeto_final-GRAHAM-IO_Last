import os
import json
import pandas as pd
import unicodedata
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import playsound

# 1. Configuração de Caminhos e Cliente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

# Mantém a tua chave original
client = OpenAI(api_key="SUA_CHAVE_AQUI")

recognizer = sr.Recognizer()

# --- FUNÇÕES DE APOIO ---

def normalizar_nome(texto):
    """Remove acentos, transforma em minúsculas e troca espaços por sublinhado"""
    if not texto: return ""
    # Remove acentos (João -> Joao)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_limpo = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Limpa pontuação e espaços
    return texto_limpo.strip().lower().replace(" ", "_").replace(".", "").replace("!", "")

def carregar_dados_usuario(nome_dito):
    """Identifica a pasta do usuário e processa saldo (Entradas - Saídas)"""
    try:
        nome_busca = normalizar_nome(nome_dito)
        print(f"DEBUG: A procurar pasta para o termo: '{nome_busca}'")
        
        # Lista as pastas em data/
        pastas_reais = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
        
        # Procura a pasta que contém o nome dito (Ex: 'joao' bate em 'joao_silva')
        pasta_encontrada = None
        for p in pastas_reais:
            if nome_busca in p:
                pasta_encontrada = p
                break
        
        if not pasta_encontrada:
            print(f"DEBUG: Nenhuma pasta encontrada para '{nome_busca}'. Pastas disponíveis: {pastas_reais}")
            return None, None, 0

        caminho_base = os.path.join(DATA_PATH, pasta_encontrada)

        # 1. Carregar Perfil
        with open(os.path.join(caminho_base, 'perfil_investidor.json'), 'r', encoding='utf-8') as f:
            perfil = json.load(f)
        
        # 2. Carregar Produtos (Ficheiro geral na raiz de data/)
        with open(os.path.join(DATA_PATH, 'produtos_financeiros.json'), 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            
        # 3. Cálculo de Saldo CORRIGIDO
        transacoes = pd.read_csv(os.path.join(caminho_base, 'transacoes.csv'))
        # Se tipo for saída, o valor fica negativo
        transacoes['valor_calculado'] = transacoes.apply(
            lambda x: x['valor'] if str(x['tipo']).lower() == 'entrada' else -x['valor'], axis=1
        )
        saldo_real = transacoes['valor_calculado'].sum()
        
        return perfil, produtos, saldo_real
    except Exception as e:
        print(f"\n[ERRO]: Falha ao processar dados: {e}")
        return None, None, 0

def falar(texto, nome_arquivo="v_temp.mp3"):
    try:
        print(f"\nGRAHAM-IO: {texto}")
        tts = gTTS(text=texto, lang='pt-br')
        tts.save(nome_arquivo)
        playsound.playsound(nome_arquivo)
        if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
    except Exception as e: print(f"Erro áudio: {e}")

def ouvir(timeout=10):
    with sr.Microphone() as source:
        print(f"\n[GRAHAM-IO está a ouvir...]")
        try:
            # Captura com mais tempo para o nome
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=12)
            with open("t_audio.wav", "wb") as f: f.write(audio.get_wav_data())
            with open("t_audio.wav", "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
            
            # Não removemos o t_audio.wav aqui para que possas conferir se falhar
            print(f"DEBUG: O Whisper ouviu: '{transcript.text}'")
            return transcript.text
        except Exception as e:
            print(f"ERRO Captura/Whisper: {e}")
            return None

def pensar(entrada, historico):
    historico.append({"role": "user", "content": entrada})
    response = client.chat.completions.create(model="gpt-4o-mini", messages=historico, temperature=0.5)
    resposta = response.choices[0].message.content
    historico.append({"role": "assistant", "content": resposta})
    return resposta

# --- FLUXO PRINCIPAL ---

if __name__ == "__main__":
    # Calibração do Microfone
    with sr.Microphone() as source:
        print("A ajustar ruído ambiente... Fica em silêncio.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        recognizer.energy_threshold = 300 # Sensibilidade manual

    falar("Olá, sou o GRAHAM-IO. Diz o teu nome completo para aceder à tua conta.")
    
    nome_dito = ouvir(timeout=10)

    if nome_dito:
        perfil, produtos, saldo = carregar_dados_usuario(nome_dito)

        if perfil:
            # Prompt de Sistema com os dados reais e corrigidos
            SYSTEM_PROMPT = f"""
            És o GRAHAM-IO, consultor do Bradesco. 
            CLIENTE: {perfil['nome']} | PERFIL: {perfil['perfil_investidor']}
            SALDO REAL CALCULADO: R$ {saldo:.2f} | PRODUTOS: {json.dumps(produtos)}
            REGRAS: Máximo 4 frases. Segue Benjamin Graham. Menciona o saldo real no início.
            """
            historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            falar(f"Acesso concedido. {perfil['nome']}, o teu saldo consolidado é de {saldo:.2f} reais. Como posso ajudar o teu perfil {perfil['perfil_investidor']} hoje?")

            while True:
                pergunta = ouvir(timeout=7)
                if pergunta:
                    print(f"TU: {pergunta}")
                    if any(p in pergunta.lower() for p in ["sair", "tchau", "obrigado", "encerrar"]):
                        falar("Até breve! Investe sempre com margem de segurança.")
                        break
                    falar(pensar(pergunta, historico_conversa))
                else:
                    print("... (A aguardar interação)")
        else:
            falar("Desculpa, não encontrei uma pasta de dados correspondente a esse nome.")
    else:
        falar("Não consegui ouvir o nome. Reinicia o sistema, por favor.")