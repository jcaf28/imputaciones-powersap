# PATH: backend/app/api/routes/agregar_imputaciones_inmemory.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse
import uuid
import asyncio
import pandas as pd
from io import BytesIO

from app.core.sse_manager import sse_manager
from app.db.session import database_session
from app.services.etl_inmemory.transformar_datos_excel_inmemory import transformar_datos_excel_inmemory
from app.services.etl_inmemory.load_datos_excel_inmemory import load_datos_excel_inmemory

router = APIRouter()

VALIDATED_DFS_IMPUT = {}  # token => DataFrame en memoria

@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, detail="El archivo debe ser .xlsx")

    content = await file.read()
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        if df.empty:
            raise ValueError("El Excel está vacío")
    except Exception as e:
        raise HTTPException(400, detail=f"Error procesando el archivo: {str(e)}")

    token = str(uuid.uuid4())
    VALIDATED_DFS_IMPUT[token] = df

    return {"message": "Archivo válido", "token": token}

@router.post("/start")
async def start_imputaciones_inmemory(
    token: str = Query(...),
    background_tasks: BackgroundTasks = None
):
    if token not in VALIDATED_DFS_IMPUT:
        raise HTTPException(400, detail="Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    df_validado = VALIDATED_DFS_IMPUT[token]
    background_tasks.add_task(long_running_inmemory, process_id, df_validado, token)

    return {"process_id": process_id}

@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            event = sse_manager.pop_next_event(process_id)
            if event:
                etype, data = event
                yield f"event: {etype}\ndata: {data}\n\n"
                if etype in ("completed", "cancelled", "error"):
                    break
            else:
                await asyncio.sleep(0.4)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/cancel/{process_id}")
async def cancel_process(process_id: str):
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}

def long_running_inmemory(process_id: str, df: pd.DataFrame, token: str):
    try:
        sse_manager.send_message(process_id, f"📁 Archivo con {len(df)} filas recibido en memoria.")
        sse_manager.send_message(process_id, "🔄 Transformando datos (inmemory)...")

        df_transformado = transformar_datos_excel_inmemory(df)

        sse_manager.send_message(process_id, "💾 Cargando datos en la BD (inmemory)...")
        nuevos_registros = 0
        with database_session as db:
            nuevos_registros = load_datos_excel_inmemory(df_transformado, sse_process_id=process_id)

        # Limpia la memoria
        if token in VALIDATED_DFS_IMPUT:
            del VALIDATED_DFS_IMPUT[token]

        sse_manager.mark_completed(process_id, f"✅ Proceso finalizado. Insertados {nuevos_registros} registros.")
    except Exception as e:
        if token in VALIDATED_DFS_IMPUT:
            del VALIDATED_DFS_IMPUT[token]
        sse_manager.mark_error(process_id, f"Error: {str(e)}")
