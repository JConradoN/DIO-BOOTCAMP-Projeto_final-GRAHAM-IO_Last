# DIO-BOOTCAMP-Projeto_final-GRAHAM-IO

# 🏦 GRAHAM-IO: Consultoria Financeira Proativa de Voz

O **GRAHAM-IO** é um agente de Inteligência Artificial consultiva desenvolvido para o desafio final do bootcamp. Baseado na filosofia de *Value Investing* de Benjamin Graham, o agente atua de forma proativa, analisando dados reais para sugerir alocações com foco em **Margem de Segurança**.

---

## 🚀 Visão Geral e Caso de Uso
Diferente de assistentes virtuais comuns, o GRAHAM-IO resolve a "paralisia de decisão". Ele antecipa necessidades ao:

1. **Identificar o usuário pela voz** e carregar seu contexto específico.
2. **Calcular o saldo real** dinamicamente através do histórico de transações.
3. **Personalizar sugestões** com base no perfil de risco (Conservador, Moderado ou Arrojado).
4. **Priorizar a segurança financeira**, sugerindo a reserva de emergência antes de ativos de risco.

---

## 🏗️ Estrutura do Repositório
O projeto está organizado seguindo as melhores práticas de versionamento e as diretrizes do curso:

```text
📁 DIO-BOOTCAMP-GRAHAM-IO/
├── 📄 requirements.txt              # Dependências do sistema
├── 📄 system_prompt.txt             # Prompt mestre da persona
├── 📄 CHANGELOG.md                  # Registro de evolução das versões
│
├── 📁 src/                          # Código Fonte Original
│   └── 📄 GRAHAM-IO_v017.py         # Versão Final Estável da Aplicação
│
├── 📁 data/                         # Base de conhecimento (Dados Mockados)
│   ├── 📁 [usuario]/                # Dados privados e logs por cliente
│   └── 📄 produtos_financeiros.json # Catálogo oficial de ativos
│
├── 📁 docs/                         # Documentação obrigatória (Entregáveis)
│   ├── 01-documentacao-agente.md
│   ├── 02-base-conhecimento.md
│   ├── 03-prompts.md
│   ├── 04-metricas.md
│   └── 05-pitch.md
│
├── 📁 versions/                     # Arquivo histórico de versões (v001 a v012)
└── 📁 assets/                       # Diagramas e recursos visuais
```
## 🛠️ Stack Tecnológica
LLM: OpenAI GPT-4o-mini (Cérebro e Tom de Voz).

Voz: OpenAI Whisper-1 (STT) e gTTS (TTS) com injeção de autoplay.

Interface: Streamlit (Dashboard financeiro).

Dados: Pandas para processamento de CSV/JSON.

🛡️ Segurança e Anti-Alucinação
Para garantir a confiabilidade exigida no setor financeiro, implementamos:

Grounding Estrito: A IA só recomenda produtos presentes no arquivo oficial de produtos.

Few-Shot Prompting: Exemplos no System Prompt que ensinam o agente a recusar perguntas fora de escopo (ex: receitas ou suporte técnico).

Logs de Auditoria: Todas as interações são gravadas automaticamente na pasta de cada cliente para rastreabilidade.

⚙️ Como Instalar e Rodar
Clonar o Repositório:

Bash
git clone [https://github.com/seu-usuario/DIO-BOOTCAMP-Projeto_final-GRAHAM-IO.git](https://github.com/seu-usuario/DIO-BOOTCAMP-Projeto_final-GRAHAM-IO.git)
cd DIO-BOOTCAMP-Projeto_final-GRAHAM-IO
Instalar Dependências:

Bash
pip install -r requirements.txt
Configurar API Key:
Abra o arquivo src/GRAHAM-IO_v017.py e insira sua chave da OpenAI na variável client = OpenAI(api_key="SUA_CHAVE_AQUI").

Executar a Aplicação:

Bash
streamlit run src/GRAHAM-IO_v017.py
📄 Documentação do Desafio
Os documentos detalhados de cada etapa podem ser acessados na pasta /docs.

Projeto desenvolvido para o Bootcamp de IA Generativa.
