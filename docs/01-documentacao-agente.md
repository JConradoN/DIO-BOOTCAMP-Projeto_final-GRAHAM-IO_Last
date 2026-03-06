# Documentação do Agente: GRAHAM-IO

## Caso de Uso
O **GRAHAM-IO** é um Agente Financeiro Proativo de Voz projetado para clientes Bradesco. Ele resolve a paralisia de decisão de investidores através de uma interface conversacional que utiliza a filosofia de *Value Investing*. O agente identifica saldos ociosos e sugere alocações focadas em "Margem de Segurança".

## Persona e Tom de Voz
- **Nome:** GRAHAM-IO
- **Personalidade:** Consultor Sênior de Investimentos, sereno e conservador.
- **Comunicação:** Técnica, porém acessível. Respostas curtas (máx. 40 palavras) para fluidez no áudio.

## Arquitetura (v017)
```mermaid
flowchart TD
    A[Usuário: Voz/Texto] -->|Streamlit Interface| B[Whisper STT]
    B --> C[Orquestrador Python]
    C --> D[Grounding: data/ + system_prompt.txt]
    D --> E[LLM: GPT-4o-mini]
    E --> F[Síntese de Voz: gTTS]
    F --> G[Saída: Áudio Base64 + Chat]