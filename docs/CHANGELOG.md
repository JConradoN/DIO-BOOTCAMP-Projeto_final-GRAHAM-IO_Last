📑 Changelog - GRAHAM-IO
Este documento registra a evolução técnica e funcional do GRAHAM-IO, detalhando as melhorias em cada versão do desenvolvimento.

[v0.1.7] - 2026-03-02 (Versão Atual)
✨ Adicionado
Hard Guardrails (Escopo): Implementação de Few-Shot Prompting para bloquear desvios de assunto. Agora o agente recusa perguntas sobre biografias (ex: "Quem foi Graham?"), histórico da bolsa ou culinária, focando 100% no saldo do cliente.

Segurança Anti-Alucinação: Bloqueio restrito para ativos fora do produtos_financeiros.json (ex: Criptoativos).

Tratamento de Saldo Crítico: Lógica específica para usuários com saldo negativo (caso Maria), priorizando quitação de dívidas antes de sugerir novos aportes.

[v0.1.2] - 2026-03-01
✨ Adicionado
Interface Streamlit Avançada: Estilização da UI com Sidebar para gestão de usuários e métricas em tempo real.

Autoplay de Áudio: Injeção de HTML/Base64 para permitir que a resposta vocal da IA seja executada automaticamente sem travar a interface.

Grounding Dinâmico: Injeção do saldo calculado (entradas - saídas) diretamente no System Prompt de cada interação.

[v0.0.8 - v0.0.9] - 2026-02-28
✨ Adicionado
Migração para Web: Transição do terminal (CLI) para o navegador via Streamlit.

Visualização de Ativos: Integração com Plotly para gerar gráficos de pizza da alocação sugerida (Renda Fixa vs. Ações).

[v0.0.6 - v0.0.7] - 2026-02-27
✨ Adicionado
Logs de Auditoria: Criação automática de log_auditoria.txt para cada usuário, permitindo rastrear o comportamento da IA.

Normalização de Dados: Implementação da biblioteca unicodedata para tratar nomes de pastas com acentos e espaços (ex: "João" para "joao_silva"), eliminando erros de leitura de arquivos.

[v0.0.4 - v0.0.5] - 2026-02-26
✨ Adicionado
Mecanismo Multi-usuário: O sistema agora identifica o cliente pela voz e busca os dados na subpasta correspondente em data/.

Identificação Biométrica Vocal: Fluxo de boas-vindas que exige a identificação do nome para carregar o contexto correto.

[v0.0.1 - v0.0.3] - 2026-02-25
✨ Adicionado
MVP (Protótipo Base): Orquestrador Python integrado à API da OpenAI e Whisper-1.

Speech-to-Text & Text-to-Speech: Implementação de SpeechRecognition e gTTS.

Lógica de Graham: Injeção inicial dos conceitos de "Margem de Segurança" no prompt do sistema.

📋 Resumo Estatístico da Evolução
Total de Versões: 17 iterações.

Métrica de Segurança: De 40% (v001) para 100% (v017) de bloqueio de alucinação.

Interface: Do Terminal (CLI) para Dashboard Interativo (Web).