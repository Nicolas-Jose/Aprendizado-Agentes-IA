# Mentoria - Projeto de Agentes

Este repositório reúne implementações de agentes de IA com integração de ferramentas, fluxos de agendamento no Google Calendar e uma API em FastAPI.

## Estrutura

- `Agents/`: notebooks e scripts Python com diferentes arquiteturas de agentes.
- `AgentFastAPI/`: camada de API para execução de agentes por endpoint HTTP.
- `.env.example`: variáveis de ambiente necessárias para execução local.
- `.gitignore`: regras de versionamento para arquivos locais e sensíveis.

## Conteúdo do projeto

- Implementações de agentes com abordagem multitool e supervisor.
- Fluxos de autenticação e leitura/escrita de eventos no Google Calendar.
- Exemplos com execução tradicional e streaming.
- Documentação de conceitos e práticas em `Agents/LEARNINGS.md`.

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

## Configuração local

- Utilize `.env` para variáveis de ambiente locais.
- Mantenha `credentials.json` e `token.json` apenas no ambiente local.
