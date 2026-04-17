# AgentFastAPI

API FastAPI para execução de agente por endpoint HTTP.

## Arquivos

- `app.py`: endpoints da API (`/health` e `/agent/run`).
- `schemas.py`: modelos Pydantic de request/response.
- `requirements.txt`: dependências mínimas da API.

## Observações

- O import em `app.py` espera um módulo `agent.py` com função `run_agent`.
- Se esse módulo não existir nesta pasta, ajuste o import para o script correto do projeto.
