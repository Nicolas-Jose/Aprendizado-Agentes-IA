# Aprendizados do Projeto (Agents)

Este documento resume o que foi aprendido em cada artefato principal para facilitar apresentação e evolução no GitHub.

## Notebooks principais

- `agente_mentoria.ipynb`
  - Aprendizado: composição de ferramentas com fluxo mais completo de agente.
  - Aprendizado: estruturação de raciocínio por etapas para tarefas de mentoria.

- `notebook_explicativo.ipynb`
  - Aprendizado: documentação didática do fluxo de agentes.
  - Aprendizado: como explicar setup e execução para terceiros.

- `agente_multitool_basico.ipynb`
  - Aprendizado: uso básico de múltiplas tools em um único agente.
  - Aprendizado: separação entre prompt, tools e execução.

- `agente_multitool_streaming.ipynb`
  - Aprendizado: streaming de resposta em tempo real.
  - Aprendizado: diferença prática entre execução síncrona e incremental.

- `agente_supervisor_fastapi.ipynb`
  - Aprendizado: padrão supervisor para orquestrar especialistas.
  - Aprendizado: preparação de lógica para exposição via API.

- `agente_traducao_calculo.ipynb`
  - Aprendizado: roteamento por intenção (tradução vs cálculo).
  - Aprendizado: padronização de saída para respostas consistentes.

- `agente_calendar_debug.ipynb`
  - Aprendizado: diagnóstico de fluxo com logs detalhados.
  - Aprendizado: validação de chamadas de ferramenta e transições de estado.

- `agent_experimento_base.ipynb`
  - Aprendizado: sandbox para testes rápidos sem afetar versões principais.

## Scripts Python

- `agente_supervisor_fastapi.py`
  - Aprendizado: arquitetura supervisor + subagentes com endpoint FastAPI.
  - Aprendizado: desacoplamento entre tool de domínio e camada HTTP.

- `agent_google_calendar_2tools.py`
  - Aprendizado: integração com Google Calendar via duas tools principais.
  - Aprendizado: fluxo de sugestão de horários e confirmação de agenda.

- `agent_google_calendar_stateful.py`
  - Aprendizado: máquina de estados explícita (`collect`, `choose`, `confirm`).
  - Aprendizado: redução de ambiguidade em conversas de agendamento.

- `teste_auth_google.py`
  - Aprendizado: autenticação OAuth local e persistência de token.

- `test_list_events.py`
  - Aprendizado: leitura de eventos para validar credenciais e conectividade.

## Melhorias de engenharia aplicadas

- Padronização de nomes para facilitar manutenção e busca.
- Remoção de redundâncias e checkpoints automáticos.
- Organização para publicação segura (com `.gitignore` e `.env.example`).
- Retirada de segredos hardcoded dos scripts principais.
