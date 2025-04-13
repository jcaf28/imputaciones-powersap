# PATH: backend/app/api/routes/agregar_imputaciones_inmemory.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse, FileResponse
import uuid
import asyncio
import pandas as pd
import os
from io import BytesIO

from app.core.sse_manager import sse_manager
from app.db.session import database_session
from app.services.etl_inmemory.transformar_datos_excel_inmemory import transformar_datos_excel_inmemory
from app.services.etl_inmemory.load_datos_excel_inmemory import load_datos_excel_inmemory

router = APIRouter()

VALIDATED_DFS_IMPUT = {}   # token => DataFrame en memoria
COMPLETED_FILES = {}       # process_id => path del Excel final (o bytes in memory)


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
    # Eliminamos ya el df para no guardarlo post-run
    del VALIDATED_DFS_IMPUT[token]

    background_tasks.add_task(long_running_inmemory, process_id, df_validado)

    return {"process_id": process_id}


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    SSE: Envía logs en tiempo real hasta que termine, se cancele o haya error.
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
                await asyncio.sleep(0.4)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cancel/{process_id}")
async def cancel_process(process_id: str):
    """
    Marca el proceso SSE como cancelado.
    """
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


@router.get("/download/{process_id}")
async def download_imputaciones(process_id: str):
    """
    Devuelve el Excel final con las columnas extra ("Status", "error_message").
    """
    if process_id not in COMPLETED_FILES:
        return {"error": "No se encontró un archivo final para ese process_id"}
    
    filepath = COMPLETED_FILES[process_id]

    # Opcional: Borrar el archivo tras servirlo
    # from fastapi.responses import FileResponse
    response = FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return response


def long_running_inmemory(process_id: str, df: pd.DataFrame):
    """
    1) Transformar en memoria
    2) Cargar en BD con contadores
    3) Crear Excel final con columnas Status/error_message
    4) Ofrecer SSE summary
    """
    try:
        total_filas = len(df)
        sse_manager.send_message(process_id, f"📁 Archivo con {total_filas} filas recibido en memoria.")
        
        sse_manager.send_message(process_id, "🔄 Transformando datos (inmemory)...")
        df_transformado = transformar_datos_excel_inmemory(df)

        sse_manager.send_message(process_id, "💾 Cargando datos en la BD (inmemory)...")

        # Aquí obtendremos summary y df_result (con columns Status, error_message)
        summary = {
            "total": total_filas,
            "success": 0,
            "fail": 0
        }

        df_result = load_datos_excel_inmemory(df_transformado, sse_process_id=process_id, summary=summary)

        # Guardar df_result en un Excel temporal
        import tempfile
        import time
        tmpdir = tempfile.gettempdir()
        filename = f"imputaciones_{process_id}_{int(time.time())}.xlsx"
        filepath = os.path.join(tmpdir, filename)
        df_result.to_excel(filepath, index=False)

        # Guardar en el diccionario
        COMPLETED_FILES[process_id] = filepath

        # Mensaje final
        mensaje_final = ( f"✅ Proceso finalizado. "
                          f"Filas totales: {summary['total']}, "
                          f"exitosas: {summary['success']}, "
                          f"fallidas: {summary['fail']}.")
        sse_manager.mark_completed(process_id, mensaje_final)
    except Exception as e:
        sse_manager.mark_error(process_id, f"Error: {str(e)}")
