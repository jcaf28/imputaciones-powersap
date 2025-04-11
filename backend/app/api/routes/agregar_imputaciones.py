# PATH: backend/app/api/routes/agregar_imputaciones.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse
import uuid
import asyncio
import pandas as pd
from io import BytesIO

from app.core.sse_manager import sse_manager
# Si tienes tu session DB
from app.db.session import database_session

# Este será tu diccionario en memoria (sin pickle)
VALIDATED_DFS_IMPUT = {}

router = APIRouter()

@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    """
    Sube un archivo Excel, se valida en memoria, no se guarda a disco.
    Devuelve un 'token' para luego iniciar el proceso.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, detail="El archivo debe ser .xlsx")

    content = await file.read()
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        # Sencilla validación: chequear que no esté vacío
        if df.empty:
            raise ValueError("El Excel está vacío o no tiene datos.")
    except Exception as e:
        raise HTTPException(400, detail=f"Error procesando el archivo: {str(e)}")

    # Guardar DF en memoria
    token = str(uuid.uuid4())
    VALIDATED_DFS_IMPUT[token] = df

    return {"message": "Archivo válido", "token": token}

@router.post("/start")
async def start_imputaciones_process(
    token: str = Query(...),
    background_tasks: BackgroundTasks = None
):
    """
    Inicia el proceso SSE con el DF ya validado (sin disco).
    """
    if token not in VALIDATED_DFS_IMPUT:
        raise HTTPException(400, detail="Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    # Recuperar DF en memoria
    df_validado = VALIDATED_DFS_IMPUT[token]

    # Lanzas la tarea en segundo plano
    background_tasks.add_task(long_running_fake, process_id, df_validado, token)

    return {"process_id": process_id}

@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    SSE: envía logs hasta que termine o se cancele.
    """
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
                await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/cancel/{process_id}")
async def cancel_process(process_id: str):
    """
    Cancela el proceso (marca el SSE como cancelado).
    """
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


def long_running_fake(process_id: str, df_excel: pd.DataFrame, token: str):
    """
    Fake: simula transform + load en memoria, sin ficheros en disco,
    solo logs SSE y finaliza sin hacer nada real.
    """
    try:
        # Mensaje 1
        sse_manager.send_message(process_id, f"Archivo con {len(df_excel)} filas validado en memoria.")
        # Simulamos transform
        sse_manager.send_message(process_id, "Transformando datos (fake)...")
        import time
        time.sleep(2)  # simula un retardo de 2 segundos

        # Simulamos load
        sse_manager.send_message(process_id, "Cargando datos (fake)...")
        time.sleep(2)

        # Borrar el DF de memoria para limpiar
        if token in VALIDATED_DFS_IMPUT:
            del VALIDATED_DFS_IMPUT[token]

        sse_manager.mark_completed(process_id, "Proceso finalizado (fake).")
    except Exception as e:
        if token in VALIDATED_DFS_IMPUT:
            del VALIDATED_DFS_IMPUT[token]
        sse_manager.mark_error(process_id, f"Error: {str(e)}")
