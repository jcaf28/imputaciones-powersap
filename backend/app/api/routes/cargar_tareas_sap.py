# PATH: backend/app/api/routes/cargar_tareas_sap.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse
import uuid
import asyncio
import pandas as pd
from io import BytesIO
import time

from app.core.sse_manager import sse_manager
from app.db.session import database_session
from app.models.models import SapOrders
from app.services.sap_etl_utils import verificar_columnas_excel, transformar_datos_sap, cargar_datos_sap_en_db

import os
import uuid
import pandas as pd

router = APIRouter()

REQUIRED_COLUMNS = ["Operation Activity", "Effectivity", "Order"]
VALIDATED_DFS  = {}  # dict[str, bytes]

@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    # Leer en memoria
    content = await file.read()
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        verificar_columnas_excel(df, REQUIRED_COLUMNS)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el archivo: {str(e)}")

    # Guardar DF en memoria (no bytes)
    token = str(uuid.uuid4())
    VALIDATED_DFS[token] = df

    return {"message": "Archivo válido", "token": token}

@router.post("/start")
async def start_carga_tareas_sap(
    token: str = Query(...),
    background_tasks: BackgroundTasks = None
):
    if token not in VALIDATED_DFS:
        raise HTTPException(status_code=400, detail="Token no encontrado o archivo no validado")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    # Recuperamos el DF validado
    df_validado = VALIDATED_DFS[token]

    # Lanzas la tarea en segundo plano
    background_tasks.add_task(long_running_task, process_id, df_validado, token)

    return {"process_id": process_id}


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    Envía los eventos SSE al frontend hasta que el proceso termine o sea cancelado.
    """
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
async def cancel_process(process_id: str):
    """
    Cancela la carga (marca el proceso como cancelado).
    """
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


def long_running_task(process_id: str, df_excel: pd.DataFrame, token: str):
    try:
        sse_manager.send_message(process_id, f"📈 DataFrame con {len(df_excel)} filas recuperado de memoria.")

        sse_manager.send_message(process_id, "🔄 Transformando datos SAP...")
        df_transformed = transformar_datos_sap(df_excel)

        sse_manager.send_message(process_id, "💾 Insertando en la base de datos...")
        with database_session as db:
            nuevos = cargar_datos_sap_en_db(df_transformed, db, process_id)
            if nuevos > 0:
                sse_manager.send_message(process_id, f"🟢 Insertados {nuevos} nuevos registros en SAPOrders.")
            else:
                sse_manager.send_message(process_id, "🟡 No se encontraron registros nuevos para insertar.")

        # Al final, eliminamos de la memoria para no ocupar espacio
        if token in VALIDATED_DFS:
            del VALIDATED_DFS[token]

        sse_manager.mark_completed(process_id, "🏁 Proceso finalizado. Insertados {nuevos} nuevos registros en SAPOrders.")
    except Exception as e:
        if token in VALIDATED_DFS:
            del VALIDATED_DFS[token]
        sse_manager.mark_error(process_id, f"Error: {str(e)}")

@router.post("/discard")
def discard_file(token: str = Query(...)):
    """
    Descarta el archivo validado de la memoria, si existe.
    """
    if token in VALIDATED_DFS:
        del VALIDATED_DFS[token]
        return {"message": "Archivo descartado"}
    return {"message": "No se encontró un archivo con ese token"}
