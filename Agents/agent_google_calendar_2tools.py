import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "LANGCHAIN_API_KEY_AQUI"
os.environ["LANGCHAIN_PROJECT"] = "pr-warmhearted-address-66"
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
# STATE (mÃ¡quina de estados explÃ­cita)
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
# TOOL 1 â€” buscar slots
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
            return json.dumps({"error": "Sem horÃ¡rios candidatos."}, ensure_ascii=False)

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

        lines = [f"{i+1}) {s.strftime('%H:%M')}â€“{e.strftime('%H:%M')}" for i, (s, e) in enumerate(free)]

        return json.dumps({
            "found": len(free),
            "text": "\n".join(lines),
            "slots": STATE["last_slots"]
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# =========================================================
# TOOL 2 â€” criar evento
# =========================================================
@tool
def calendar_create_event_from_slot(
    option_number: int,
    summary: str = "Atendimento tÃ©cnico",
    calendar_id: str = DEFAULT_CALENDAR_ID,
) -> str:
    try:
        service = get_calendar_service()

        slots = STATE.get("last_slots") or []
        if option_number < 1 or option_number > len(slots):
            return json.dumps({"error": "OpÃ§Ã£o invÃ¡lida."}, ensure_ascii=False)

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
VocÃª Ã© um agente de agendamento.

ESTADO ATUAL:
- phase: {STATE["phase"]}
- last_query: {STATE["last_query"]}
- slots_salvos: {len(STATE["last_slots"])}
- selected_option: {STATE["selected_option"]}

REGRAS DE TRANSIÃ‡ÃƒO (OBRIGATÃ“RIAS):

1) phase=collect
- Objetivo: coletar data (YYYY-MM-DD), preferÃªncia de horÃ¡rio e duraÃ§Ã£o.
- Converter preferÃªncia em janela:
  * "antes das HH" -> 08:00â€“HH:00
  * "depois das HH" -> HH:00â€“21:00
  * "entre HH e HH" -> HH:00â€“HH:00
- Chamar calendar_find_available_slots.

2) phase=choose
- Se o usuÃ¡rio enviar APENAS um nÃºmero (1, 2 ou 3), isso Ã© a escolha da opÃ§Ã£o.
- NÃƒO pedir data novamente.
- ApÃ³s escolher, confirmar explicitamente:
  "Confirmo o horÃ¡rio <HH:MM>. Posso agendar? (sim/nÃ£o)"

3) phase=confirm
- Se o usuÃ¡rio responder "sim/confirmo", chamar calendar_create_event_from_slot.
- Se responder "nÃ£o", voltar para phase=choose.

Regras gerais:
- Nunca reinicie a coleta se phase != collect.
- Nunca invente horÃ¡rios sem chamar calendar_find_available_slots.
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
        user_in = input("VocÃª: ").strip()
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

