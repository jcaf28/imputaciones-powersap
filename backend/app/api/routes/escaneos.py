# PATH: backend/app/api/routes/escaneos.py

import uuid
import os
import asyncio

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse

from app.core.sse_manager import sse_manager
from app.services.seguimiento_escaneos_service import process_escaneos_logic

router = APIRouter()

@router.post("/start")
async def start_escaneo_process(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Inicia el proceso de seguimiento de escaneos (subida + análisis).
    Devuelve un process_id para poder escuchar los eventos SSE y descargar el resultado.
    """
    process_id = str(uuid.uuid4())
    file_location = f"/tmp/{process_id}_{file.filename}"

    # Guardar el archivo subido en /tmp (o donde tú quieras).
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # Iniciar el proceso en SSEManager
    sse_manager.start_process(process_id)

    # Agregar la tarea en segundo plano que hará el procesamiento principal
    background_tasks.add_task(long_running_escaneo_task, process_id, file_location)

    return {"process_id": process_id}


async def long_running_escaneo_task(process_id: str, file_location: str):
    """
    Ejemplo de tarea larga que llama a la lógica central 
    (generar_archivo_orden_cerrar) y va notificando por SSE.
    """
    try:
        state = sse_manager.get_state(process_id)
        if not state:
            return  # El proceso no existe o se ha limpiado

        # Llamada a la lógica principal:
        result_path = await process_escaneos_logic(process_id, file_location)

        # Si el proceso no fue cancelado, marcamos como completado
        if not state["cancelled"]:
            sse_manager.mark_completed(
                process_id,
                "Proceso de seguimiento de escaneos completado con éxito",
                result_file=result_path
            )

    except Exception as e:
        sse_manager.mark_error(process_id, f"Error en el procesamiento: {str(e)}")


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    Stream de eventos SSE al frontend hasta que el proceso termine, se cancele o falle.
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
    Cancela el proceso y notifica vía SSE.
    """
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


@router.get("/download/{process_id}")
async def download_escaneo_result(process_id: str, background_tasks: BackgroundTasks):
    """
    Descarga el archivo resultante (xlsx) y luego lo borra.
    """
    state = sse_manager.get_state(process_id)
    if not state:
        return {"error": "Process ID no encontrado"}

    if state["status"] != "completed":
        return {"error": f"No está completado (status = {state['status']})"}

    result_file = state.get("result_file")
    if not result_file or not os.path.exists(result_file):
        return {"error": "No se encontró el archivo resultante"}

    background_tasks.add_task(os.remove, result_file)

    return FileResponse(
        path=result_file,
        filename=os.path.basename(result_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=background_tasks
    )
