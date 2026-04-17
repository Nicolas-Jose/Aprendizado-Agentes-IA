import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

if os.getenv("LANGCHAIN_TRACING_V2") is None:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
# =========================================================
# CONFIG
# =========================================================
TIMEZONE = "America/Sao_Paulo"
TZ = ZoneInfo(TIMEZONE)
DEFAULT_CALENDAR_ID = "primary"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

# =========================================================
# STATE (máquina de estados explícita)
# =========================================================
STATE: Dict[str, Any] = {
    "phase": "collect",   # collect | choose | confirm
    "last_query": None,   # {date, window_start, window_end, duration_min}
    "last_slots": [],     # [{"start": iso, "end": iso}]
    "selected_option": None,
}

# =========================================================
# GOOGLE SERVICE
# =========================================================
def get_calendar_service():
    if not hasattr(get_calendar_service, "_service"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        get_calendar_service._service = build("calendar", "v3", credentials=creds)
    return get_calendar_service._service

# =========================================================
# HELPERS
# =========================================================
def make_dt(date_str: str, hhmm: str) -> datetime:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    h, m = map(int, hhmm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)

def overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1

def list_events(service, calendar_id, start, end):
    resp = service.events().list(
        calendarId=calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=250,
    ).execute()
    return resp.get("items", [])

def event_interval(e):
    s = e.get("start", {})
    en = e.get("end", {})
    if "dateTime" not in s or "dateTime" not in en:
        return None
    return datetime.fromisoformat(s["dateTime"]), datetime.fromisoformat(en["dateTime"])

# =========================================================
# TOOL 1 — buscar slots
# =========================================================
@tool
def calendar_find_available_slots(
    date: str,
    window_start: str,
    window_end: str,
    duration_min: int = 60,
    step_min: int = 15,
    calendar_id: str = DEFAULT_CALENDAR_ID,
) -> str:
    """
    Busca até 3 horários disponíveis no Google Calendar dentro de uma janela de tempo.

    Use esta ferramenta para verificar disponibilidade antes de agendar.
    Retorna uma lista numerada de horários livres.
    """
    try:

        service = get_calendar_service()

        start_dt = make_dt(date, window_start)
        end_dt = make_dt(date, window_end)
        dur = timedelta(minutes=duration_min)
        step = timedelta(minutes=step_min)

        candidates = []
        cur = start_dt
        while cur + dur <= end_dt:
            candidates.append((cur, cur + dur))
            cur += step

        if not candidates:
            return json.dumps({"error": "Sem horários candidatos."}, ensure_ascii=False)

        events = list_events(service, calendar_id, start_dt, end_dt)
        busy = []
        for e in events:
            iv = event_interval(e)
            if iv:
                busy.append(iv)

        free = []
        for s, e in candidates:
            if not any(overlaps(s, e, b0, b1) for b0, b1 in busy):
                free.append((s, e))
            if len(free) == 3:
                break

        STATE["last_query"] = {
            "date": date,
            "window_start": window_start,
            "window_end": window_end,
            "duration_min": duration_min,
        }
        STATE["last_slots"] = [{"start": s.isoformat(), "end": e.isoformat()} for s, e in free]
        STATE["phase"] = "choose"
        STATE["selected_option"] = None

        lines = [f"{i+1}) {s.strftime('%H:%M')}–{e.strftime('%H:%M')}" for i, (s, e) in enumerate(free)]

        return json.dumps({
            "found": len(free),
            "text": "\n".join(lines),
            "slots": STATE["last_slots"]
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# =========================================================
# TOOL 2 — criar evento
# =========================================================
@tool
def calendar_create_event_from_slot(
    option_number: int,
    summary: str = "Atendimento técnico",
    calendar_id: str = DEFAULT_CALENDAR_ID,
) -> str:
    """
    Cria um evento no Google Calendar usando a opção escolhida (1, 2 ou 3).

    Só deve ser usada após confirmação explícita do usuário.
    """
    try:
        service = get_calendar_service()

        slots = STATE.get("last_slots") or []
        if option_number < 1 or option_number > len(slots):
            return json.dumps({"error": "Opção inválida."}, ensure_ascii=False)

        chosen = slots[option_number - 1]
        start_dt = datetime.fromisoformat(chosen["start"])
        end_dt = datetime.fromisoformat(chosen["end"])

        body = {
            "summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
        }

        created = service.events().insert(calendarId=calendar_id, body=body).execute()

        STATE["phase"] = "collect"
        STATE["last_slots"] = []
        STATE["selected_option"] = None

        return json.dumps({
            "status": created.get("status"),
            "htmlLink": created.get("htmlLink")
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# =========================================================
# PROMPT COM STATE INJECTION
# =========================================================
def system_prompt_with_state() -> str:
    return f"""
Você é um agente de agendamento.
hoje é {datetime.now().strftime("%Y-%m-%d")}
regra: amanhã é {datetime.now().strftime("%Y-%m-%d")} + 1 dia
ESTADO ATUAL:
- phase: {STATE["phase"]}
- last_query: {STATE["last_query"]}
- slots_salvos: {len(STATE["last_slots"])}
- selected_option: {STATE["selected_option"]}

REGRAS DE TRANSIÇÃO (OBRIGATÓRIAS):

1) phase=collect (coleta incremental):
- Você deve coletar somente o que estiver faltando no ESTADO ATUAL.
- Campos necessários para buscar horários:
  1) date (YYYY-MM-DD)
  2) duration_min (se não informado, assumir 60)
  3) window_start e window_end (se não informado, assumir 08:00 e 21:00)

- Se date já estiver presente no estado, NÃO peça date novamente.
- Se duration_min já estiver presente, NÃO peça duration novamente.
- Se o usuário fornecer preferência de horário (ex.: "depois das 12"), você deve:
  * converter para window_start/window_end
  * e então chamar imediatamente calendar_find_available_slots usando os valores do estado.

- Se faltar apenas a preferência de horário, peça apenas isso.
- Não ofereça opções fixas (como “antes/depois das 10”). Aceite "antes das HH", "depois das HH", "entre HH e HH", "qualquer horário".

2) phase=choose
- Se o usuário enviar APENAS um número (1, 2 ou 3), isso é a escolha da opção.
Quando o usuário escolher uma opção (1/2/3), você DEVE:
- salvar selected_option = esse número
- mudar para phase=confirm
- confirmar usando o slot em STATE.last_slots[selected_option-1]
Nunca confirme “por aproximação” (por exemplo, sempre 14:00). Use exatamente o start/end do slot escolhido.
  "Confirmo o horário <HH:MM>. Posso agendar? (sim/não)"

3) phase=confirm
- Se o usuário responder "sim/confirmo", chamar calendar_create_event_from_slot.
- Se responder "não", voltar para phase=choose.

Regras gerais:
- Nunca reinicie a coleta se phase != collect.
- Nunca invente horários sem chamar calendar_find_available_slots.
"""

# =========================================================
# MAIN
# =========================================================
def main():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
        [calendar_find_available_slots, calendar_create_event_from_slot],
        tool_choice="auto",
    )

    agent = create_agent(
        llm,
        tools=[calendar_find_available_slots, calendar_create_event_from_slot],
        system_prompt=system_prompt_with_state(),
    )

    print("Agente pronto. Digite 'sair' para encerrar.\n")

    while True:
        user_in = input("Você: ").strip()
        if user_in.lower() in {"sair", "exit", "quit"}:
            break

        agent = create_agent(
            llm,
            tools=[calendar_find_available_slots, calendar_create_event_from_slot],
            system_prompt=system_prompt_with_state(),
        )

        result = agent.invoke({"messages": [{"role": "user", "content": user_in}]})
        print("\nAgente:", result["messages"][-1].content, "\n")

if __name__ == "__main__":
    main()

