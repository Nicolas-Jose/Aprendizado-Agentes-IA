# Pasta Agents

Esta pasta concentra os artefatos ativos de experimentação com agentes.

## Conteúdo ativo

### Notebooks

- `agente_mentoria.ipynb`
- `notebook_explicativo.ipynb`
- `agente_multitool_basico.ipynb`
- `agente_multitool_streaming.ipynb`
- `agente_supervisor_fastapi.ipynb`
- `agente_traducao_calculo.ipynb`
- `agente_calendar_debug.ipynb`
- `agent_experimento_base.ipynb`

### Scripts

- `agente_supervisor_fastapi.py`: supervisor com especialistas e endpoint FastAPI.
- `agent_google_calendar_2tools.py`: busca de horários e criação de eventos no Google Calendar.
- `agent_google_calendar_stateful.py`: agendamento com máquina de estados.
- `teste_auth_google.py`: bootstrap de autenticação OAuth local.
- `test_list_events.py`: verificação de leitura de eventos.

## Limpeza já aplicada

- Remoção de notebooks redundantes/legados:
  - `AgentFinal.ipynb`
  - `AgentFinal2.ipynb`
  - `AgentGPT.ipynb`
  - `MultiAgent.ipynb`
- Remoção de checkpoints automáticos em `.ipynb_checkpoints/`.
- Padronização de nomes para legibilidade e consistência.

## Documentação de aprendizados

- Consulte `LEARNINGS.md` para resumo do que foi aprendido em cada arquivo principal.

## Observações de segurança

- `credentials.json`, `token.json` e `.env` são locais e não devem ser versionados.
- Para produção, use variáveis de ambiente e/ou secret manager.
