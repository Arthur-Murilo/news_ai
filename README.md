# News AI

Workflow simples em Python para pesquisar noticias com Tavily, sintetizar o conteudo com Gemini e gerar uma newsletter em HTML enviada por email com Resend.

## O que o projeto faz

O fluxo principal executa tres etapas em sequencia:

1. `pesquisador`: busca noticias recentes sobre o assunto informado.
2. `formatador`: transforma o material pesquisado em uma newsletter pronta para envio.
3. `enviar_email`: dispara o HTML final por email via Resend.

O pipeline e orquestrado com LangGraph em [`src/main.py`](src/main.py).

## Requisitos

- Python 3.13+
- `uv` para instalar dependencias e executar os comandos
- Chaves validas para Google Gemini, Tavily e Resend

## Instalacao

```bash
uv sync
```

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env-example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env-example .env
```

## Variaveis de ambiente

O arquivo [`.env-example`](.env-example) documenta a configuracao minima. As variaveis usadas pelo codigo hoje sao:

- `GOOGLE_API_KEY`: chave da API do Google Gemini.
- `MODEL_AGENT_SEARCH`: modelo usado pelo agente pesquisador.
- `MODEL_AGENT_FORMATER`: modelo usado pelo agente formatador.
- `TAVILY_API_KEY`: chave da API de busca.
- `RESEND_API_KEY`: chave da API de envio de email.
- `SUBJECT`: tema inicial enviado ao grafo principal.
- `BEFORE_DAYS`: janela de dias usada na busca de noticias.
- `MAX_SEARCH_RESULTS`: limite de resultados retornados pelo Tavily.

Compatibilidade: os agentes aceitam `AI_MODEL` como fallback, mas a configuracao recomendada agora e separar os modelos por agente.

## Como executar

Executa o workflow completo:

```bash
uv run python -m src.main
```

Executa apenas o agente pesquisador de forma interativa:

```bash
uv run python -m src.agents.agent_pesquisador
```

## Estrutura do projeto

```text
src/
  agents/
    agent_formatador.py
    agent_pesquisador.py
    tools/search_tool.py
  nodes/
    node_formatador.py
    node_pesquisador.py
    node_send_email.py
  prompts/
    agent_fomatador_prompt.py
    agent_pesquisador_prompt.py
  main.py
```

## Detalhes tecnicos

- O projeto usa `MessagesState` do LangGraph para encadear as mensagens entre os nos.
- O `search_new` em [`src/agents/tools/search_tool.py`](src/agents/tools/search_tool.py) aplica busca no Tavily com `topic="news"` e filtra resultados por data.
- Cada agente e instanciado com `ChatGoogleGenerativeAI` e prompt proprio.
- O envio final acontece em [`src/nodes/node_send_email.py`](src/nodes/node_send_email.py) via `resend.Emails.send`.

## Observacoes importantes

- O remetente e o destinatario do email estao fixos no codigo atual em [`src/nodes/node_send_email.py`](src/nodes/node_send_email.py).
- O assunto usado para iniciar a pesquisa vem de `SUBJECT`; se nao existir, o valor padrao atual e `Inteligencia Artifical`.
- Ainda nao existe suite de testes. Se adicionar testes, prefira `pytest` e mocks para Gemini, Tavily e Resend.

## Dependencias principais

- `langgraph`
- `langchain`
- `langchain-google-genai`
- `tavily-python`
- `resend`
- `python-dotenv`

## Licenca

MIT. Veja [`LICENSE`](LICENSE).
