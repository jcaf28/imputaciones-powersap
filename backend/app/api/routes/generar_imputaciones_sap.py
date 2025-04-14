# PATH: backend/app/api/routes/generar_imputaciones_sap.py

from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List
import uuid
import time
import asyncio
from sqlalchemy.orm import Session

from app.db.session import database_session
from app.db.session import get_db
from app.models.models import Imputaciones

from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes, get_imputaciones_pendientes_count


router = APIRouter()

# ================== FAKE DATABASE ===================
FAKE_DATA = [
    {
        "id": 1,
        "fechaImp": "2025-04-01",
        "codEmpleado": "E123",
        "horas": 5.5,
        "proyecto": "P001",
        "tipoCoche": "A",
        "cargadoSap": False
    },
    {
        "id": 2,
        "fechaImp": "2025-04-02",
        "codEmpleado": "E124",
        "horas": 3.75,
        "proyecto": "P002",
        "tipoCoche": "C",
        "cargadoSap": False
    },
    {
        "id": 3,
        "fechaImp": "2025-04-05",
        "codEmpleado": "E555",
        "horas": 2.0,
        "proyecto": "P003",
        "tipoCoche": "B",
        "cargadoSap": False
    }
]

SESSIONS: Dict[str, Dict[str, Any]] = {}

# ================== ENDPOINTS ===================


@router.get("/list-summary")
def count_pending_imputaciones(db: Session = Depends(get_db)):
    count = get_imputaciones_pendientes_count(db)
    return {"count": count}


@router.get("/list", response_model=List[Dict[str, Any]])
def list_pending_imputaciones(db: Session = Depends(get_db)):
    return get_imputaciones_pendientes(db)

@router.post("/start")
def start_process(background_tasks: BackgroundTasks):
    process_id = str(uuid.uuid4())
    SESSIONS[process_id] = {
        "status": "in-progress",
        "logs": ["🟢 Proceso iniciado..."],
        "csv_data": b""
    }
    background_tasks.add_task(long_running_task, process_id)
    return {"process_id": process_id}


@router.post("/cancel/{process_id}")
def cancel_process(process_id: str):
    session = SESSIONS.get(process_id)
    if not session:
        raise HTTPException(404, detail="process_id no encontrado")
    if session["status"] == "in-progress":
        session["status"] = "cancelled"
        session["logs"].append("🛑 Proceso cancelado por el usuario.")
    return {"message": f"Proceso cancelado (estado actual: {session['status']})"}


@router.get("/download/{process_id}")
def download_csv(process_id: str):
    session = SESSIONS.get(process_id)
    if not session or session["status"] != "completed":
        raise HTTPException(400, detail="CSV no disponible todavía.")
    return Response(
        content=session["csv_data"],
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="imputaciones_{process_id}.csv"'
        }
    )


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    if process_id not in SESSIONS:
        raise HTTPException(404, detail="process_id no encontrado")
    last_idx = 0

    async def event_generator():
        nonlocal last_idx
        while True:
            if await request.is_disconnected():
                break

            session = SESSIONS[process_id]
            logs = session["logs"]

            while last_idx < len(logs):
                yield f"event: message\ndata: {logs[last_idx]}\n\n"
                last_idx += 1

            if session["status"] in ["completed", "cancelled", "error"]:
                yield f"event: {session['status']}\ndata: {logs[-1]}\n\n"
                break

            await asyncio.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ================== BACKGROUND TASK ===================

def long_running_task(process_id: str):
    try:
        add_log(process_id, "📥 Cargando imputaciones...")
        time.sleep(1)

        add_log(process_id, f"📝 Encontradas {len(FAKE_DATA)} imputaciones.")
        time.sleep(1)

        add_log(process_id, "📊 Generando CSV...")
        csv_header = "ID,FechaImp,Empleado,Horas,Proyecto,TipoCoche,CargadoSap\n"
        csv_rows = [
            f"{row['id']},{row['fechaImp']},{row['codEmpleado']},{row['horas']},{row['proyecto']},{row['tipoCoche']},{row['cargadoSap']}\n"
            for row in FAKE_DATA
        ]
        csv_content = csv_header + "".join(csv_rows)
        SESSIONS[process_id]["csv_data"] = csv_content.encode("utf-8")

        time.sleep(1)
        add_log(process_id, "✅ CSV generado correctamente.")
        mark_completed(process_id)

    except Exception as e:
        mark_error(process_id, f"❌ Error: {str(e)}")


# ================== HELPERS ===================

def add_log(pid, msg):
    if pid in SESSIONS and SESSIONS[pid]["status"] == "in-progress":
        SESSIONS[pid]["logs"].append(msg)

def mark_completed(pid):
    if pid in SESSIONS and SESSIONS[pid]["status"] == "in-progress":
        SESSIONS[pid]["status"] = "completed"

def mark_error(pid, msg):
    if pid in SESSIONS:
        SESSIONS[pid]["logs"].append(msg)
        SESSIONS[pid]["status"] = "error"
