import os
from fastapi import FastAPI, HTTPException

from agent import run_agent
from schemas import AgentRunRequest, AgentRunResponse

app = FastAPI(title="Mentoria Agent API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/agent/run", response_model=AgentRunResponse)
def agent_run(payload: AgentRunRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY não configurada no ambiente.")
    try:
        output = run_agent(payload.input)
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
