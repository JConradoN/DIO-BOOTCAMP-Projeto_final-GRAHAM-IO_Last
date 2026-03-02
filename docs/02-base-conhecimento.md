# Base de Conhecimento: GRAHAM-IO

## Estrutura de Dados
O agente utiliza um modelo de "Multi-Tenant" local, onde cada cliente possui seu próprio contexto:

| Arquivo | Localização | Função |
| :--- | :--- | :--- |
| `produtos_financeiros.json` | `/data/` | Catálogo oficial de ativos e taxas. |
| `perfil_investidor.json` | `/data/[cliente]/` | Define o perfil (Conservador/Arrojado) e metas. |
| `transacoes.csv` | `/data/[cliente]/` | Histórico para cálculo dinâmico de saldo. |

## Estratégia de Grounding
Os dados não são apenas "lidos", eles são injetados no `system_prompt.txt` via placeholders `{saldo}`, `{perfil}` e `{produtos_json}`. Isso garante que a IA nunca sugira um produto que não esteja no catálogo oficial.