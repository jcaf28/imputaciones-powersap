from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, Request, Query, File
from fastapi.responses import StreamingResponse, FileResponse
from app.core.sse_manager import sse_manager
from io import BytesIO
import pandas as pd
import uuid
import asyncio
import tempfile

from app.services.feedback.feedback_processor import procesar_feedback_completo

router = APIRouter()

VALIDATED_FEEDBACK = {}  # token -> DataFrame
TEMP_FILES = {}          # process_id -> temp file path

@router.post("/validate-file")
async def validate_feedback_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    content = await file.read()
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        if 'Fecha' not in df.columns:
            raise ValueError("El archivo debe contener una columna 'Fecha'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el archivo: {str(e)}")

    token = str(uuid.uuid4())
    VALIDATED_FEEDBACK[token] = df

    return {"message": "Archivo de feedback válido", "token": token}

@router.post("/start")
async def start_feedback_process(token: str = Query(...), background_tasks: BackgroundTasks = None):
    if token not in VALIDATED_FEEDBACK:
        raise HTTPException(status_code=400, detail="Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    df = VALIDATED_FEEDBACK[token]
    background_tasks.add_task(long_running_feedback_task, process_id, df, token)

    return {"process_id": process_id}

@router.get("/events/{process_id}")
async def sse_feedback_events(request: Request, process_id: str):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            event = sse_manager.pop_next_event(process_id)
            if event:
                event_type, data = event
                yield f"event: {event_type}\ndata: {data}\n\n"
                if event_type in ("completed", "cancelled", "error"):
                    break
            else:
                await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/cancel/{process_id}")
async def cancel_feedback_process(process_id: str):
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}

@router.get("/download/{process_id}")
async def download_feedback_file(process_id: str):
    if process_id not in TEMP_FILES:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(TEMP_FILES[process_id], filename="feedback_result.xlsx")

async def long_running_feedback_task(process_id: str, df: pd.DataFrame, token: str):
    try:
        sse_manager.send_message(process_id, f"📄 Procesando archivo con {len(df)} filas...")

        _, temp_file_path = procesar_feedback_completo(df, process_id)
        TEMP_FILES[process_id] = temp_file_path

        sse_manager.mark_completed(process_id, "✅ Feedback procesado. Listo para descargar.")

    except Exception as e:
        sse_manager.mark_error(process_id, f"❌ Error: {str(e)}")

    finally:
        if token in VALIDATED_FEEDBACK:
            del VALIDATED_FEEDBACK[token]

