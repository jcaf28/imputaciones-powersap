# PATH: backend/app/api/routes/generar_imputaciones_sap.py

from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List
import uuid
import time
import asyncio
from sqlalchemy.orm import Session

from app.db.session import get_db

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes, get_imputaciones_pendientes_count


router = APIRouter()

SESSIONS: Dict[str, Dict[str, Any]] = {}
COMPLETED_FILES = {}  # process_id => "/tmp/... .xlsx" o "C:/temporal/..."
# ================== ENDPOINTS ===================


@router.get("/list-summary")
def count_pending_imputaciones(db: Session = Depends(get_db)):
    count = get_imputaciones_pendientes_count(db)
    return {"count": count}


@router.get("/list", response_model=List[Dict[str, Any]])
def list_pending_imputaciones(db: Session = Depends(get_db)):
    return get_imputaciones_pendientes(db)

@router.get("/download/{process_id}")
def download_sap_result(process_id: str):
    """
    Devuelve el archivo final (Excel/CSV) tras completarse el proceso SSE.
    """
    if process_id not in COMPLETED_FILES:
        raise HTTPException(404, detail="No se encontró un archivo para ese process_id.")

    file_path = COMPLETED_FILES[process_id]
    if not os.path.exists(file_path):
        raise HTTPException(404, detail="El archivo no existe o fue eliminado.")

    # En caso de que quieras forzar la descarga como Excel, ajusta el "media_type"
    # y "filename" según tu preferencia (CSV vs XLSX).
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/start")
def start_process_sap(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    process_id = str(uuid.uuid4())
    SESSIONS[process_id] = {
        "status": "in-progress",
        "logs": [],
    }
    background_tasks.add_task(_bg_assign_sap, process_id, db)
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


# @router.get("/download/{process_id}")
# def download_csv(process_id: str):
#     session = SESSIONS.get(process_id)
#     if not session or session["status"] != "completed":
#         raise HTTPException(400, detail="CSV no disponible todavía.")
#     return Response(
#         content=session["csv_data"],
#         media_type="text/csv",
#         headers={
#             "Content-Disposition": f'attachment; filename="imputaciones_{process_id}.csv"'
#         }
#     )


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

def _bg_assign_sap(process_id: str, db: Session):
    logs = SESSIONS[process_id]["logs"]
    try:
        from app.services.generar_imputaciones_sap.assign_sap_orders import run_assign_sap_orders_inmemory
        logs.append("Iniciando la asignación de SAP Orders en TablaCentral...")

        # Llamada principal
        run_assign_sap_orders_inmemory(db, logs)

        logs.append("✅ Proceso completado. Ya puedes generar el CSV con /generate-excel (si lo deseas).")
        SESSIONS[process_id]["status"] = "completed"

    except Exception as e:
        SESSIONS[process_id]["status"] = "error"
        logs.append(f"❌ Error en _bg_assign_sap: {str(e)}")


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
