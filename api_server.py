from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

from expert_algas import KnowledgeBaseManager, AlgaeExpertSystem

app = FastAPI(title="Sistema Experto Macroalgas API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mantener sesiones sencillas en memoria
sessions: Dict[str, AlgaeExpertSystem] = {}


class StartRequest(BaseModel):
    session_id: str


class AnswerRequest(BaseModel):
    session_id: str
    character_name: str
    answer: str  # S, N, D


class FiltersRequest(BaseModel):
    session_id: str
    temp: Optional[float] = None
    salinity: Optional[float] = None
    station: Optional[str] = None
    month: Optional[int] = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "sistema-experto-macroalgas"}


@app.post("/api/diagnosis/start")
def start_diagnosis(payload: StartRequest):
    try:
        kb_manager = KnowledgeBaseManager("algae_knowledge.json")
        engine = AlgaeExpertSystem(kb_manager)
        sessions[payload.session_id] = engine
        return {"session_id": payload.session_id, "state": engine.get_state()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/diagnosis/answer")
def submit_answer(payload: AnswerRequest):
    engine = sessions.get(payload.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if payload.answer not in {"S", "N", "D", "NS"}:
        raise HTTPException(status_code=400, detail="answer debe ser S, N, D o NS")

    try:
        normalized_answer = "D" if payload.answer == "NS" else payload.answer
        engine.submit_answer(payload.character_name, normalized_answer)
        return {"session_id": payload.session_id, "state": engine.get_state()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/diagnosis/state")
def get_state(session_id: str):
    engine = sessions.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"session_id": session_id, "state": engine.get_state()}


@app.post("/api/diagnosis/filters")
def set_filters(payload: FiltersRequest):
    engine = sessions.get(payload.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    try:
        engine.set_pre_filters(payload.temp, payload.salinity, payload.station, payload.month)
        return {"session_id": payload.session_id, "state": engine.get_state()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/diagnosis/session")
def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
