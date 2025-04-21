# PATH: backend/app/api/routes/obtener_feedback.py
from fastapi import (
    APIRouter, BackgroundTasks, UploadFile, HTTPException,
    Query, Request, File, Response
)
from fastapi.responses import StreamingResponse
import uuid, asyncio
import pandas as pd
from io import BytesIO

from app.core.sse_manager import sse_manager
from app.services.feedback.obtener_feedback_service import (
    preparar_dataframe_feedback,
    generar_xlsx_en_memoria,
)

router = APIRouter()

# token  -> (DataFrame, nombre_original)
VALIDATED_DFS: dict[str, tuple[pd.DataFrame, str]] = {}
# procId -> { "filename": str, "content": bytes }
RESULTS: dict[str, dict] = {}


# ---------- 1) VALIDAR ------------------------------------------------------
@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "El archivo debe ser .xlsx")

    try:
        df = pd.read_excel(BytesIO(await file.read()), engine="openpyxl")
    except Exception as e:
        raise HTTPException(400, f"Error leyendo Excel: {e}")

    token = str(uuid.uuid4())
    VALIDATED_DFS[token] = (df, file.filename)
    return {"message": "Archivo válido", "token": token}


# ---------- 2) START --------------------------------------------------------
@router.post("/start")
async def start_obtener_feedback(
    token: str = Query(...),
    background_tasks: BackgroundTasks | None = None,
):
    if token not in VALIDATED_DFS:
        raise HTTPException(400, "Token no encontrado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    df, original_name = VALIDATED_DFS[token]

    background_tasks.add_task(
        _worker,
        process_id,
        df.copy(),           # aislamos
        original_name,
        token,
    )
    return {"process_id": process_id}


# ---------- 3) EVENTOS SSE --------------------------------------------------
@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    async def event_gen():
        while True:
            if await request.is_disconnected():
                break
            event = sse_manager.pop_next_event(process_id)
            if event:
                typ, data = event
                yield f"event: {typ}\ndata: {data}\n\n"
                if typ in ("completed", "cancelled", "error"):
                    break
            else:
                await asyncio.sleep(0.5)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ---------- 4) DESCARGAR RESULTADO -----------------------------------------
@router.get("/result/{process_id}")
async def download_result(process_id: str):
    info = RESULTS.pop(process_id, None)
    if not info:
        raise HTTPException(404, "Resultado no disponible")

    # al descargar eliminamos también de SSE manager para liberar memoria
    sse_manager.delete_process(process_id)

    return Response(
        content=info["content"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{info["filename"]}"'
        },
    )


# ---------- 5) CANCELAR -----------------------------------------------------
@router.post("/cancel/{process_id}")
async def cancel_process(process_id: str):
    if sse_manager.get_state(process_id):
        sse_manager.mark_cancelled(process_id)
        RESULTS.pop(process_id, None)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


# ---------- 6) DESCARTAR TOKEN ---------------------------------------------
@router.post("/discard")
def discard_file(token: str = Query(...)):
    VALIDATED_DFS.pop(token, None)
    return {"message": "OK"}


# ---------- 7) WORKER -------------------------------------------------------
def _worker(
    process_id: str,
    df: pd.DataFrame,
    original_name: str,
    token: str,
):
    try:
        sse_manager.send_message(process_id, f"📥 Fichero con {len(df)} filas recibido")

        sse_manager.send_message(process_id, "🛠️ Preparando datos…")
        df_prepared = preparar_dataframe_feedback(df)

        sse_manager.send_message(process_id, "🔍 Consultando base de datos…")
        filename, content_bytes = generar_xlsx_en_memoria(
            df_prepared, original_name, process_id
        )

        # limpiar memoria del token de validación
        VALIDATED_DFS.pop(token, None)

        RESULTS[process_id] = {"filename": filename, "content": content_bytes}

        sse_manager.mark_completed(
            process_id,
            f"🏁 Proceso finalizado – listo para descargar.",
        )
    except Exception as e:
        VALIDATED_DFS.pop(token, None)
        RESULTS.pop(process_id, None)
        sse_manager.mark_error(process_id, f"❌ Error: {e}")
