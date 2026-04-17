# Aprendizados do Projeto (Agents)

Este documento resume os conceitos e práticas aplicados em cada artefato principal da pasta `Agents`.

## Notebooks principais

- `agente_mentoria.ipynb`
  - Composição de ferramentas em um fluxo de agente.
  - Estruturação de raciocínio por etapas para tarefas de mentoria.

- `notebook_explicativo.ipynb`
  - Documentação didática do fluxo de agentes.
  - Estrutura de setup e execução.

- `agente_multitool_basico.ipynb`
  - Uso de múltiplas ferramentas em um único agente.
  - Separação entre prompt, ferramentas e execução.

- `agente_multitool_streaming.ipynb`
  - Streaming de resposta em tempo real.
  - Diferença entre execução síncrona e incremental.

- `agente_supervisor_fastapi.ipynb`
  - Padrão supervisor para orquestração de especialistas.
  - Preparação de lógica para exposição via API.

- `agente_traducao_calculo.ipynb`
  - Roteamento por intenção (tradução e cálculo).
  - Padronização de saída para respostas consistentes.

- `agente_calendar_debug.ipynb`
  - Diagnóstico de fluxo com logs detalhados.
  - Validação de chamadas de ferramenta e transições de estado.

- `agent_experimento_base.ipynb`
  - Estrutura base para testes e prototipagem.

## Scripts Python

- `agente_supervisor_fastapi.py`
  - Arquitetura supervisor com subagentes e endpoint FastAPI.
  - Desacoplamento entre lógica de domínio e camada HTTP.

- `agent_google_calendar_2tools.py`
  - Integração com Google Calendar por duas ferramentas principais.
  - Fluxo de sugestão de horários e confirmação de agenda.

- `agent_google_calendar_stateful.py`
  - Máquina de estados explícita (`collect`, `choose`, `confirm`).
  - Controle de contexto em conversas de agendamento.

- `teste_auth_google.py`
  - Autenticação OAuth local e persistência de token.

- `test_list_events.py`
  - Leitura de eventos para validação de credenciais e conectividade.

## Práticas de engenharia

- Padronização de nomes de arquivos.
- Organização de estrutura para navegação e manutenção.
- Uso de arquivos de configuração para execução local.
