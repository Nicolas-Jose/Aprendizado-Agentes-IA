import os

from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

# =========================
# ENV
# =========================
os.environ["OPENAI_API_KEY"] = "OPENAI_API_KEY_AQUI"  # mantenha fora do cÃ³digo em produÃ§Ã£o (use env var)

# LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "LANGCHAIN_API_KEY_AQUI"
os.environ["LANGCHAIN_PROJECT"] = "pr-warmhearted-address-66"

# =========================
# LLMs
# =========================
# Supervisor (router)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# LLM usado INTERNAMENTE pela TOOL de traduÃ§Ã£o (sem bind_tools)
llm_tradutor_interno = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# LLM do agente de cÃ¡lculo (com tools obrigatÃ³rias)
llm_calculo = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
    tools=[],
)

# =========================
# TOOLS (baixo nÃ­vel)
# =========================
@tool
def calculadora(expressao: str) -> str:
    """Ferramenta para realizar cÃ¡lculos matemÃ¡ticos."""
    try:
        resultado = eval(expressao, {"__builtins__": {}}, {})
        return f"Resultado: {resultado}"
    except Exception as e:
        return f"Erro no cÃ¡lculo: {str(e)}"


@tool
def tradutor_tool(texto: str, idioma_destino: str = "inglÃªs") -> str:
    """Ferramenta para traduzir textos usando LLM interno."""
    try:
        prompt = (
            f"Traduza o seguinte texto para {idioma_destino}. "
            f"Retorne APENAS a traduÃ§Ã£o:\n\n{texto}"
        )
        response = llm_tradutor_interno.invoke(prompt)
        return f"TraduÃ§Ã£o: {response.content.strip()}"
    except Exception as e:
        return f"Erro na traduÃ§Ã£o: {str(e)}"


# =========================
# SUBAGENTE 1: CÃLCULO
# =========================
CALCULADORA_PROMPT = """
VocÃª Ã© um assistente especializado em matemÃ¡tica e cÃ¡lculos.

REGRA OBRIGATÃ“RIA DE FORMATAÃ‡ÃƒO:
Toda resposta DEVE seguir este formato exato:
[ExplicaÃ§Ã£o detalhada do raciocÃ­nio matemÃ¡tico, ordem de operaÃ§Ãµes e processo]

[Resultado final claro e direto]

REGRAS:
- SEMPRE use a ferramenta `calculadora` para fazer os cÃ¡lculos.
- SEMPRE forneÃ§a explicaÃ§Ã£o didÃ¡tica antes do resultado.
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
# SUBAGENTE 2: TRADUÃ‡ÃƒO
# =========================
TRADUTOR_PROMPT = """
VocÃª Ã© um assistente especializado em traduÃ§Ã£o de idiomas.

REGRAS OBRIGATÃ“RIAS (NÃƒO NEGOCIÃVEIS):
1) VocÃª DEVE chamar a ferramenta `tradutor_tool` para obter a traduÃ§Ã£o.
2) VocÃª NUNCA deve produzir a traduÃ§Ã£o final usando conhecimento prÃ³prio sem chamar a ferramenta.
3) Se o usuÃ¡rio nÃ£o especificar o idioma de destino, assuma que ele quer inglÃªs.
4) Se o usuÃ¡rio pedir explicaÃ§Ã£o + traduÃ§Ã£o, primeiro obtenha a traduÃ§Ã£o via ferramenta e depois escreva o contexto.

REGRA OBRIGATÃ“RIA DE FORMATAÃ‡ÃƒO:
Toda resposta DEVE seguir este formato exato:

[ExplicaÃ§Ã£o sobre a expressÃ£o/palavra, contexto cultural ou linguÃ­stico]

[Linha em branco]

[Resultado da traduÃ§Ã£o claro e direto]
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
# TOOLS (alto nÃ­vel) - usadas pelo supervisor
# =========================
@tool
def realizar_calculo(solicitacao: str) -> str:
    """Realiza cÃ¡lculos matemÃ¡ticos com explicaÃ§Ã£o didÃ¡tica."""
    result = calculadora_agent.invoke(
        {"messages": [{"role": "user", "content": solicitacao}]}
    )
    return result["messages"][-1].content


@tool
def realizar_traducao(solicitacao: str) -> str:
    """Traduz textos entre idiomas com contexto explicativo.

    Use quando o usuÃ¡rio quiser traduzir palavras, frases ou textos
    para outros idiomas.

    Entrada: SolicitaÃ§Ã£o de traduÃ§Ã£o em linguagem natural (ex: 'traduza hello para portuguÃªs')
    """
    result = tradutor_agent.invoke({"messages": [{"role": "user", "content": solicitacao}]})
    return result["messages"][-1].content


# =========================
# SUPERVISOR
# =========================
SUPERVISOR_PROMPT = """
VocÃª Ã© um assistente inteligente que coordena especialistas em matemÃ¡tica e traduÃ§Ã£o.

VocÃª tem acesso a dois especialistas:
1. Especialista em CÃ¡lculos - para todas as operaÃ§Ãµes matemÃ¡ticas
2. Especialista em TraduÃ§Ã£o - para traduzir textos entre idiomas

IMPORTANTE:
- Quando o usuÃ¡rio pedir cÃ¡lculos, use o especialista em cÃ¡lculos.
- Quando o usuÃ¡rio pedir traduÃ§Ãµes, use o especialista em traduÃ§Ã£o.
- Se a solicitaÃ§Ã£o envolver ambos, use os dois em sequÃªncia.
- Sempre retorne a resposta completa dos especialistas, mantendo o formato explicativo.

VocÃª deve apenas coordenar e passar as solicitaÃ§Ãµes para os especialistas corretos.
Os especialistas jÃ¡ seguem o formato correto de resposta (explicaÃ§Ã£o + resultado).
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
        msg, metadata = event

        if isinstance(msg, AIMessageChunk) and msg.content:
            print(msg.content, end="", flush=True)
            resposta_final += msg.content

    return resposta_final


