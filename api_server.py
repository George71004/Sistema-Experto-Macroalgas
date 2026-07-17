import os
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from a2wsgi import ASGIMiddleware
from expert_algas import KnowledgeBaseManager, AlgaeExpertSystem
from knowledge_editor import KnowledgeBaseEditor

load_dotenv()
ADMIN_PASSWORD: str = os.getenv("ADMIN", "")

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


# â”€â”€ Admin auth dependency â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def require_admin(x_admin_password: Optional[str] = Header(default=None)):
    """Valida el header X-Admin-Password contra la variable ADMIN del .env."""
    if not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="La contraseÃ±a de administrador no estÃ¡ configurada en el servidor.",
        )
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="ContraseÃ±a de administrador incorrecta o no proporcionada.",
        )


# â”€â”€ Pydantic models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


class AdminNodeRequest(BaseModel):
    node_id: str
    is_leaf: bool
    question: Optional[str] = None
    character_name: Optional[str] = None
    yes_branch: Optional[str] = None
    no_branch: Optional[str] = None
    species_name: Optional[str] = None
    phylum: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    description: Optional[str] = None
    habitat_note: Optional[str] = None
    env_profile: Optional[Dict[str, Any]] = None


class DeleteNodeRequest(BaseModel):
    force: Optional[bool] = False


# â”€â”€ Public endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        raise HTTPException(status_code=404, detail="SesiÃ³n no encontrada")

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
        raise HTTPException(status_code=404, detail="SesiÃ³n no encontrada")
    return {"session_id": session_id, "state": engine.get_state()}


@app.post("/api/diagnosis/filters")
def set_filters(payload: FiltersRequest):
    engine = sessions.get(payload.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="SesiÃ³n no encontrada")

    try:
        engine.set_pre_filters(payload.temp, payload.salinity, payload.station, payload.month)
        return {"session_id": payload.session_id, "state": engine.get_state()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/diagnosis/retract")
def retract_answer(payload: RetractRequest):
    engine = sessions.get(payload.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="SesiÃ³n no encontrada")

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


# â”€â”€ Protected admin endpoints (require X-Admin-Password header) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/admin/nodes", dependencies=[Depends(require_admin)])
def list_nodes():
    editor = KnowledgeBaseEditor("algae_knowledge.json")
    return {"nodes": list(editor.kb.keys())}


@app.get("/api/admin/node/{node_id}", dependencies=[Depends(require_admin)])
def get_node(node_id: str):
    editor = KnowledgeBaseEditor("algae_knowledge.json")
    node = editor.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    return {"node_id": node_id, "node": node}


@app.post("/api/admin/node", dependencies=[Depends(require_admin)])
def create_or_update_node(payload: AdminNodeRequest):
    editor = KnowledgeBaseEditor("algae_knowledge.json")
    try:
        # Validate that branch nodes exist for question (non-leaf) nodes
        if not payload.is_leaf:
            if payload.yes_branch and payload.yes_branch not in editor.kb:
                raise HTTPException(
                    status_code=400,
                    detail=f"El nodo yes_branch '{payload.yes_branch}' no existe en la base de conocimiento."
                )
            if payload.no_branch and payload.no_branch not in editor.kb:
                raise HTTPException(
                    status_code=400,
                    detail=f"El nodo no_branch '{payload.no_branch}' no existe en la base de conocimiento."
                )

        node = editor.upsert_node(
            payload.node_id,
            payload.is_leaf,
            question=payload.question,
            character_name=payload.character_name,
            yes_branch=payload.yes_branch,
            no_branch=payload.no_branch,
            species_name=payload.species_name,
            phylum=payload.phylum,
            order=payload.order,
            family=payload.family,
            description=payload.description,
            habitat_note=payload.habitat_note,
            env_profile=payload.env_profile or {}
        )
        editor.save_kb()
        return {"node_id": payload.node_id, "node": node, "status": "created_or_updated"}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/admin/node/{node_id}", dependencies=[Depends(require_admin)])
def delete_node(node_id: str, force: bool = False):
    editor = KnowledgeBaseEditor("algae_knowledge.json")
    try:
        referencing = editor.delete_node_by_id(node_id, force=force)
        editor.save_kb()
        return {"node_id": node_id, "status": "deleted", "references": referencing}
    except KeyError:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    except ValueError as exc:
        detail = exc.args[0] if exc.args else str(exc)
        raise HTTPException(status_code=409, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
