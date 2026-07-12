from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from a2wsgi import ASGIMiddleware
from expert_algas import KnowledgeBaseManager, AlgaeExpertSystem

app = FastAPI(title="Sistema Experto Macroalgas API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

wsgi_app = ASGIMiddleware(app)

# Mantener sesiones sencillas en memoria
sessions: Dict[str, AlgaeExpertSystem] = {}


class StartRequest(BaseModel):
    session_id: str


class AnswerRequest(BaseModel):
    session_id: str
    character_name: str
    answer: str  # S, N, NS


class FiltersRequest(BaseModel):
    session_id: str
    temp: Optional[float] = None
    salinity: Optional[float] = None
    station: Optional[Any] = None
    month: Optional[Any] = None


class RetractRequest(BaseModel):
    session_id: str
    character_name: str


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

    if payload.answer not in {"S", "N", "NS"}:
        raise HTTPException(status_code=400, detail="answer debe ser S, N o NS")

    try:
        engine.submit_answer(payload.character_name, payload.answer)
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


@app.post("/api/diagnosis/retract")
def retract_answer(payload: RetractRequest):
    engine = sessions.get(payload.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    try:
        engine.retract_choice(payload.character_name)
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
