# PATH: backend/app/api/routes/generar_imputaciones_sap.py

from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from typing import Dict, Any, List
import uuid
import time
import asyncio
import traceback
from sqlalchemy.orm import Session

from app.db.session import get_db

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.models.models import TablaCentral
from app.services.generar_imputaciones_sap.assign_sap_orders import run_assign_sap_orders_inmemory
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

@router.get("/download")
def download_sap_csv_zip(db: Session = Depends(get_db)):
    """
    Genera un .zip con CSV + XLSX y lo devuelve.
    """
    from app.services.generar_imputaciones_sap.generar_csv import generate_zip_with_csv_and_xlsx
    zip_path = generate_zip_with_csv_and_xlsx(db)

    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(404, detail="No se pudo generar el ZIP (quizá sin registros).")

    return FileResponse(
        path=zip_path,
        filename=os.path.basename(zip_path),
        media_type="application/octet-stream"
    )


@router.post("/start")
def start_process_sap(
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    db: Session = Depends(get_db)
):
    if not force:
        pending_count = db.query(TablaCentral).filter(TablaCentral.Cargado_SAP == False).count()
        if pending_count > 0:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Hay {pending_count} filas pendientes de respuesta SAP. Si continúas, se eliminarán y podrían generar duplicados en SAP.",
                    "pending_count": pending_count
                }
            )

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
                final_data = logs[-1] if logs else ""
                if session["status"] == "completed":
                    mc = session.get("matched_count", 0)
                    final_data = f"{mc}"
                yield f"event: {session['status']}\ndata: {final_data}\n\n"
                break

            await asyncio.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ================== BACKGROUND TASK ===================

def _bg_assign_sap(process_id: str, db: Session):
    logs = SESSIONS[process_id]["logs"]
    try:
        logs.append("Iniciando la asignación de SAP Orders en TablaCentral...")

        # Llamada principal
        matched = run_assign_sap_orders_inmemory(db, logs)

        if matched and matched > 0:
            logs.append(f"✅ Proceso completado con {matched} asignaciones. Ya puedes descargar el ZIP.")
        else:
            logs.append("⚠️ Proceso completado pero sin asignaciones. Revisa los logs para más detalle.")
        SESSIONS[process_id]["status"] = "completed"
        SESSIONS[process_id]["matched_count"] = matched or 0

    except Exception as e:
        SESSIONS[process_id]["status"] = "error"
        tb = traceback.format_exc()
        logs.append(f"❌ Error en _bg_assign_sap: {str(e)}\n{tb}")
        print(f"[generar_imputaciones_sap] ERROR: {str(e)}\n{tb}", flush=True)


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
