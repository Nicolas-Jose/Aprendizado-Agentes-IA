# Mentoria - Projeto de Agentes

Este repositório reúne experimentos com agentes LLM, integração com Google Calendar e uma API com FastAPI.

## Estrutura

- `Agents/`: notebooks e scripts de experimentação com agentes.
- `AgentFastAPI/`: API para expor agente por endpoint HTTP.
- `.gitignore`: proteção contra versionamento de credenciais, tokens e ambientes locais.

## Organização aplicada

- Renomeação de arquivos com nomes descritivos.
- Padronização para nomes sem espaços.
- Remoção de chaves sensíveis hardcoded em scripts Python.
- Preparação do projeto para publicação segura no GitHub.
- Remoção de arquivos redundantes e checkpoints automáticos.
- Inclusão de documentação de aprendizados em `Agents/LEARNINGS.md`.

## Como executar (visão geral)

1. Crie um ambiente virtual Python.
2. Instale dependências:
   - `pip install -r AgentFastAPI/requirements.txt`
3. Configure variáveis de ambiente necessárias:
   - `OPENAI_API_KEY`
   - `LANGCHAIN_API_KEY` (se usar tracing/projeto no LangSmith)
   - `LANGCHAIN_PROJECT` (opcional)
4. Execute a API:
   - `uvicorn AgentFastAPI.app:app --reload`

## Segurança

- Não suba `credentials.json`, `token.json`, `.env` ou chaves de API para o GitHub.
- Revogue e gere novas chaves sempre que alguma tiver sido exposta em arquivos locais.
