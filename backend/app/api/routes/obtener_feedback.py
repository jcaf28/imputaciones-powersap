from fastapi import (
    APIRouter,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Request,
    Query,
    File,
)
from fastapi.responses import StreamingResponse, FileResponse
from app.core.sse_manager import sse_manager
from io import BytesIO
import pandas as pd, uuid, asyncio

from app.services.feedback.feedback_processor import procesar_feedback_completo

router = APIRouter()

# token -> { df, filename }
VALIDATED_FEEDBACK = {}
# process_id -> { path, download_name }
TEMP_FILES = {}

# ---------------------------------------------------------------------
@router.post("/validate-file")
async def validate_feedback_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "El archivo debe ser .xlsx")

    content = await file.read()
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        if "Fecha" not in df.columns:
            raise ValueError("El archivo debe contener una columna 'Fecha'")
    except Exception as e:
        raise HTTPException(400, f"Error procesando el archivo: {e}")

    token = str(uuid.uuid4())
    VALIDATED_FEEDBACK[token] = {"df": df, "filename": file.filename}
    return {"message": "Archivo de feedback válido", "token": token}

# ---------------------------------------------------------------------
@router.post("/start")
async def start_feedback_process(
    token: str = Query(...),
    background_tasks: BackgroundTasks = None,
):
    if token not in VALIDATED_FEEDBACK:
        raise HTTPException(400, "Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    payload = VALIDATED_FEEDBACK[token]
    background_tasks.add_task(
        long_running_feedback_task,
        process_id,
        payload["df"],
        payload["filename"],
        token,
    )
    return {"process_id": process_id}

# ---------------------------------------------------------------------
@router.get("/events/{process_id}")
async def sse_feedback_events(request: Request, process_id: str):
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

# ---------------------------------------------------------------------
@router.post("/cancel/{process_id}")
async def cancel_feedback_process(process_id: str):
    if sse_manager.get_state(process_id):
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}

# ---------------------------------------------------------------------
@router.get("/download/{process_id}")
async def download_feedback_file(process_id: str):
    if process_id not in TEMP_FILES:
        raise HTTPException(404, "Archivo no encontrado")

    info = TEMP_FILES.pop(process_id)   # elimina después de servir
    return FileResponse(info["path"], filename=info["download_name"])

# ---------------------------------------------------------------------
async def long_running_feedback_task(
    process_id: str,
    df: pd.DataFrame,
    original_filename: str,
    token: str,
):
    try:
        sse_manager.send_message(
            process_id, f"📄 Procesando archivo con {len(df)} filas…"
        )

        path, download_name = procesar_feedback_completo(
            df, process_id, original_filename
        )
        TEMP_FILES[process_id] = {"path": path, "download_name": download_name}

        sse_manager.mark_completed(
            process_id, "✅ Feedback procesado. Listo para descargar."
        )
    except Exception as e:
        sse_manager.mark_error(process_id, f"❌ Error: {e}")
    finally:
        VALIDATED_FEEDBACK.pop(token, None)
