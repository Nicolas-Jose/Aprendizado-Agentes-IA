from pydantic import BaseModel, Field

class AgentRunRequest(BaseModel):
    input: str = Field(..., min_length=1, examples=["Traduza 'hello' para português e calcule 7*8"])

class AgentRunResponse(BaseModel):
    output: str
