# PATH: backend/app/api/routes/cargar_tareas_sap.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse
import uuid
import asyncio
import pandas as pd
from io import BytesIO

from app.core.sse_manager import sse_manager
from app.db.session import database_session
from app.models.models import SapOrders
from app.services.sap_etl_utils import verificar_columnas_excel, transformar_datos_sap, cargar_datos_sap_en_db

import os
import uuid
import pandas as pd

router = APIRouter()

REQUIRED_COLUMNS = ["Operation Activity", "Effectivity", "Order"]

@router.post("/validate-file")
async def validate_file(file: UploadFile = File(...)):
    """
    Sube un archivo Excel, lo guarda temporalmente y valida que contenga las columnas necesarias.
    Si algo falla, se lanza excepción con HTTP 400.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    import uuid, os

    # Ruta temporal
    tmp_path = f"/tmp/validate_{uuid.uuid4()}_{file.filename}"
    try:
        # Guardar a disco
        with open(tmp_path, "wb") as f_out:
            content = await file.read()
            f_out.write(content)

        # Leer desde disco (más rápido que usar BytesIO)
        df = pd.read_excel(tmp_path, engine="openpyxl")

        # Validar columnas requeridas
        verificar_columnas_excel(df, REQUIRED_COLUMNS)

        return {"message": "Archivo válido"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el archivo: {str(e)}")

    finally:
        # Limpieza del archivo temporal
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/start")
async def start_carga_tareas_sap(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Inicia la carga de datos SAP (transform + load) usando SSE para informar progreso.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    process_id = str(uuid.uuid4())
    sse_manager.start_process(process_id)

    # Leemos el contenido *una vez* y se lo pasamos al background task
    content = await file.read()

    # Agregamos la tarea en segundo plano
    background_tasks.add_task(long_running_task, process_id, content)

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


def long_running_task(process_id: str, file_content: bytes):
    try:
        sse_manager.send_message(process_id, "Guardando Excel en disco temporal...")
        tmp_path = f"/tmp/{uuid.uuid4()}.xlsx"
        with open(tmp_path, "wb") as temp_file:
            temp_file.write(file_content)

        sse_manager.send_message(process_id, "Leyendo datos Excel...")
        # Opcional: leer solo las columnas que necesitas
        df_excel = pd.read_excel(
            tmp_path, 
            engine="openpyxl",
            usecols=["Operation Activity","Effectivity","Order"]
        )
        os.remove(tmp_path)

        verificar_columnas_excel(df_excel, ["Operation Activity","Effectivity","Order"])
        sse_manager.send_message(process_id, "Transformando datos...")

        df_transformed = transformar_datos_sap(df_excel)

        sse_manager.send_message(process_id, "Cargando datos en la base de datos...")
        with database_session as db:
            cargar_datos_sap_en_db(df_transformed, db)

        sse_manager.mark_completed(process_id, "¡Proceso completado con éxito!")
    except Exception as e:
        sse_manager.mark_error(process_id, f"Error: {str(e)}")
