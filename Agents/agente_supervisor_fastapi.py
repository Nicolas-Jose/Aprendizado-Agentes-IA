import os

from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

# =========================
# ENV
# =========================
# Segurança: nunca versionar chaves no código.
if os.getenv("LANGCHAIN_TRACING_V2") is None:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

# =========================
# LLMs
# =========================
# Supervisor (router)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# LLM usado INTERNAMENTE pela TOOL de tradução (sem bind_tools)
llm_tradutor_interno = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# LLM do agente de cálculo (com tools obrigatórias)
llm_calculo = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
    tools=[],
)

# =========================
# TOOLS (baixo nível)
# =========================
@tool
def calculadora(expressao: str) -> str:
    """Ferramenta para realizar cálculos matemáticos."""
    try:
        resultado = eval(expressao, {"__builtins__": {}}, {})
        return f"Resultado: {resultado}"
    except Exception as e:
        return f"Erro no cálculo: {str(e)}"


@tool
def tradutor_tool(texto: str, idioma_destino: str = "inglês") -> str:
    """Ferramenta para traduzir textos usando LLM interno."""
    try:
        prompt = (
            f"Traduza o seguinte texto para {idioma_destino}. "
            f"Retorne APENAS a tradução:\n\n{texto}"
        )
        response = llm_tradutor_interno.invoke(prompt)
        return f"Tradução: {response.content.strip()}"
    except Exception as e:
        return f"Erro na tradução: {str(e)}"


# =========================
# SUBAGENTE 1: CÁLCULO
# =========================
CALCULADORA_PROMPT = """
Você é um assistente especializado em matemática e cálculos.

REGRA OBRIGATÓRIA DE FORMATAÇÃO:
Toda resposta DEVE seguir este formato exato:
[Explicação detalhada do raciocínio matemático, ordem de operações e processo]

[Resultado final claro e direto]

REGRAS:
- SEMPRE use a ferramenta `calculadora` para fazer os cálculos.
- SEMPRE forneça explicação didática antes do resultado.
"""

llm_calculo_agent = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
    [calculadora],
    tool_choice="required",
)

calculadora_agent = create_agent(
    llm_calculo_agent,
    tools=[calculadora],
    system_prompt=CALCULADORA_PROMPT,
)

# =========================
# SUBAGENTE 2: TRADUÇÃO
# =========================
TRADUTOR_PROMPT = """
Você é um assistente especializado em tradução de idiomas.

REGRAS OBRIGATÓRIAS (NÃO NEGOCIÁVEIS):
1) Você DEVE chamar a ferramenta `tradutor_tool` para obter a tradução.
2) Você NUNCA deve produzir a tradução final usando conhecimento próprio sem chamar a ferramenta.
3) Se o usuário não especificar o idioma de destino, assuma que ele quer inglês.
4) Se o usuário pedir explicação + tradução, primeiro obtenha a tradução via ferramenta e depois escreva o contexto.

REGRA OBRIGATÓRIA DE FORMATAÇÃO:
Toda resposta DEVE seguir este formato exato:

[Explicação sobre a expressão/palavra, contexto cultural ou linguístico]

[Linha em branco]

[Resultado da tradução claro e direto]
"""

# LLM do agente tradutor (OBRIGA tool)
llm_tradutor_agent = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
    [tradutor_tool],
    tool_choice="required",
)

tradutor_agent = create_agent(
    llm_tradutor_agent,
    tools=[tradutor_tool],
    system_prompt=TRADUTOR_PROMPT,
)

# =========================
# TOOLS (alto nível) - usadas pelo supervisor
# =========================
@tool
def realizar_calculo(solicitacao: str) -> str:
    """Realiza cálculos matemáticos com explicação didática."""
    result = calculadora_agent.invoke(
        {"messages": [{"role": "user", "content": solicitacao}]}
    )
    return result["messages"][-1].content


@tool
def realizar_traducao(solicitacao: str) -> str:
    """Traduz textos entre idiomas com contexto explicativo.

    Use quando o usuário quiser traduzir palavras, frases ou textos
    para outros idiomas.

    Entrada: Solicitação de tradução em linguagem natural (ex: 'traduza hello para português')
    """
    result = tradutor_agent.invoke({"messages": [{"role": "user", "content": solicitacao}]})
    return result["messages"][-1].content


# =========================
# SUPERVISOR
# =========================
SUPERVISOR_PROMPT = """
Você é um assistente inteligente que coordena especialistas em matemática e tradução.

Você tem acesso a dois especialistas:
1. Especialista em Cálculos - para todas as operações matemáticas
2. Especialista em Tradução - para traduzir textos entre idiomas

IMPORTANTE:
- Quando o usuário pedir cálculos, use o especialista em cálculos.
- Quando o usuário pedir traduções, use o especialista em tradução.
- Se a solicitação envolver ambos, use os dois em sequência.
- Sempre retorne a resposta completa dos especialistas, mantendo o formato explicativo.

Você deve apenas coordenar e passar as solicitações para os especialistas corretos.
Os especialistas já seguem o formato correto de resposta (explicação + resultado).
"""

supervisor_agent = create_agent(
    llm,
    tools=[realizar_calculo, realizar_traducao],
    system_prompt=SUPERVISOR_PROMPT,
)

# =========================
# RUNNERS
# =========================
def run_agent(user_input: str) -> str:
    """Executa o supervisor e retorna a resposta final."""
    messages = [{"role": "user", "content": user_input}]
    result = supervisor_agent.invoke({"messages": messages})
    return result["messages"][-1].content


def run_agent_stream(user_input: str) -> str:
    """Executa o supervisor com streaming palavra por palavra."""
    messages = [{"role": "user", "content": user_input}]

    resposta_final = ""

    for event in supervisor_agent.stream({"messages": messages}, stream_mode="messages"):
        msg, _metadata = event

        if isinstance(msg, AIMessageChunk) and msg.content:
            print(msg.content, end="", flush=True)
            resposta_final += msg.content

    return resposta_final

# =========================
# FASTAPI
# =========================
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AgentRequest(BaseModel):
    user_input: str

class AgentResponse(BaseModel):
    response: str

@app.post("/agent", response_model=AgentResponse)
async def agent_endpoint(payload: AgentRequest):
    resposta = run_agent(payload.user_input)
    return AgentResponse(response=resposta)


