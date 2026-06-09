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
- `NEWSLETTER_FROM_EMAIL`: remetente usado no envio do email.
- `NEWSLETTER_TO_EMAIL`: destinatario usado no envio do email.
- `SUBJECT`: tema inicial enviado ao grafo principal.
- `BEFORE_DAYS`: janela de dias usada na busca de noticias. Faixa valida: `1` a `30`.
- `MAX_SEARCH_RESULTS`: limite de resultados retornados pelo Tavily. Faixa valida: `1` a `20`.
- `SCHEDULE_FREQUENCY`: frequencia do scheduler do container. Valores validos: `daily`, `weekly`, `monthly`.
- `SCHEDULE_HOUR`: hora de execucao no timezone `America/Sao_Paulo`. Faixa valida: `0` a `23`.
- `SCHEDULE_WEEKDAY`: usado apenas quando `SCHEDULE_FREQUENCY=weekly`. Faixa valida: `1` a `7`, com `1=segunda` e `7=domingo`.
- `SCHEDULE_DAY`: usado apenas quando `SCHEDULE_FREQUENCY=monthly`. Faixa valida: `1` a `31`.

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

Executa o scheduler continuo localmente:

```bash
uv run python -m src.scheduler
```

## Agendamento

O container fica ativo continuamente e executa o workflow conforme a configuracao por ambiente.

- `daily`: executa todos os dias na hora definida por `SCHEDULE_HOUR`.
- `weekly`: executa uma vez por semana no dia definido por `SCHEDULE_WEEKDAY` e na hora definida por `SCHEDULE_HOUR`.
- `monthly`: executa uma vez por mes no dia definido por `SCHEDULE_DAY` e na hora definida por `SCHEDULE_HOUR`.

O timezone de execucao e fixo em `America/Sao_Paulo`.

Exemplos:

```env
SCHEDULE_FREQUENCY=daily
SCHEDULE_HOUR=9
```

```env
SCHEDULE_FREQUENCY=weekly
SCHEDULE_WEEKDAY=1
SCHEDULE_HOUR=8
```

```env
SCHEDULE_FREQUENCY=monthly
SCHEDULE_DAY=15
SCHEDULE_HOUR=7
```

## Docker

Build da imagem:

```bash
docker build -t news-ai .
```

Execucao com variaveis do `.env`:

```bash
docker run --rm --env-file .env news-ai
```

Se quiser validar sem esperar o horario agendado, rode o workflow uma vez no container:

```bash
docker run --rm --env-file .env --entrypoint python news-ai -m src.main
```

Se quiser so confirmar que as variaveis entraram sem expor os valores, use:

```bash
docker run --rm --env-file .env --entrypoint python news-ai -c "import os; print(all(os.getenv(k) for k in ['GOOGLE_API_KEY','TAVILY_API_KEY','RESEND_API_KEY']))"
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
  scheduler.py
  security.py
```

## Detalhes tecnicos

- O projeto usa `MessagesState` do LangGraph para encadear as mensagens entre os nos.
- O `search_new` em [`src/agents/tools/search_tool.py`](src/agents/tools/search_tool.py) aplica busca no Tavily com `topic="news"`, valida a janela de datas e remove links inseguros antes de devolver resultados ao agente.
- Cada agente e instanciado com `ChatGoogleGenerativeAI` e prompt proprio.
- O envio final acontece em [`src/nodes/node_send_email.py`](src/nodes/node_send_email.py) via `resend.Emails.send`, com sanitizacao do HTML e filtragem de links e imagens inseguras.

## Observacoes importantes

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
