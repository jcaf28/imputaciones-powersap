# PATH: backend/app/api/routes/cargar_respuesta_sap.py

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
import uuid, asyncio

import pandas as pd
from io import BytesIO

from app.core.sse_manager import sse_manager
from app.services.sap_response_handling.actualizar_cargado_sap import procesar_respuesta_sap

router = APIRouter(
    tags=["cargar-respuesta-sap"],
)

# Almacenamos el binario en memoria → token:string ➜ bytes
VALIDATED_FILES: dict[str, bytes] = {}


# ---------- 1) VALIDAR ----------
@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx / .xls")

    content = await file.read()

    try:
        # Simple check: ¿se puede abrir con pandas?
        pd.read_excel(BytesIO(content), engine="openpyxl")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el archivo: {e}")

    token = str(uuid.uuid4())
    VALIDATED_FILES[token] = content
    return {"message": "Archivo válido", "token": token}


# ---------- 2) START ----------
@router.post("/start")
async def start_process(
    token: str = Query(...),
    background_tasks: BackgroundTasks = None,
):
    if token not in VALIDATED_FILES:
        raise HTTPException(status_code=400, detail="Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    # Lanza la tarea en segundo plano
    background_tasks.add_task(long_running_task, process_id, VALIDATED_FILES[token], token)
    return {"process_id": process_id}


# ---------- 3) EVENTOS SSE ----------
@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            event = sse_manager.pop_next_event(process_id)
            if event:
                ev_type, data = event
                yield f"event: {ev_type}\ndata: {data}\n\n"

                if ev_type in ("completed", "cancelled", "error"):
                    break
            else:
                await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------- 4) CANCEL ----------
@router.post("/cancel/{process_id}")
def cancel_process(process_id: str):
    if sse_manager.get_state(process_id):
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


# ---------- 5) DESCARTAR ----------
@router.post("/discard")
def discard_file(token: str = Query(...)):
    if token in VALIDATED_FILES:
        del VALIDATED_FILES[token]
        return {"message": "Archivo descartado"}
    return {"message": "No se encontró un archivo con ese token"}


# ---------- LONG‑RUNNING ----------
def long_running_task(process_id: str, file_bytes: bytes, token: str):
    try:
        sse_manager.send_message(process_id, "🔄 Creando archivo temporal…")
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            copyfileobj(BytesIO(file_bytes), tmp)
            tmp_path = tmp.name

        sse_manager.send_message(process_id, "⚙️ Procesando respuesta SAP…")
        ok = procesar_respuesta_sap(tmp_path)

        # Limpiar token en memoria
        VALIDATED_FILES.pop(token, None)

        if ok:
            sse_manager.mark_completed(process_id, "✅ Procesamiento completado correctamente.")
        else:
            sse_manager.mark_error(process_id, "❌ Error al procesar la respuesta SAP.")
    except Exception as e:
        VALIDATED_FILES.pop(token, None)
        sse_manager.mark_error(process_id, f"❌ Error: {e}")
