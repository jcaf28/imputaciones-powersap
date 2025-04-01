# PATH: backend/app/api/routes/cnc.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
import uuid
import os
import asyncio

from app.core.sse_manager import sse_manager
from app.services.cnc_processor import process_cnc_logic  # Tu lógica principal

router = APIRouter()

@router.post("/start")
async def start_cnc_process(file: UploadFile, background_tasks: BackgroundTasks):
    process_id = str(uuid.uuid4())
    file_location = f"/tmp/{process_id}_{file.filename}"

    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # Iniciamos el proceso en SSEManager
    sse_manager.start_process(process_id)

    # Agregamos la tarea en segundo plano que hará el procesamiento
    background_tasks.add_task(long_running_task, process_id, file_location)

    return {"process_id": process_id}


async def long_running_task(process_id: str, file_location: str):
    try:
        state = sse_manager.get_state(process_id)
        if not state:
            return  # Proceso no existe

        # Llamada a la lógica principal
        result_path = await process_cnc_logic(process_id, file_location)

        # Si no se ha cancelado
        if not state["cancelled"]:
            sse_manager.mark_completed(process_id, "Proceso completado con éxito", result_file=result_path)

    except Exception as e:
        sse_manager.mark_error(process_id, f"Error en el procesamiento: {str(e)}")


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    Enviamos eventos SSE al frontend hasta que el proceso termine, se cancele o haya error.
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            # Tomamos el siguiente evento de la cola
            event = sse_manager.pop_next_event(process_id)
            if event:
                event_type, data = event

                yield f"event: {event_type}\ndata: {data}\n\n"

                # Si es completed / cancelled / error, terminamos
                if event_type in ("completed", "cancelled", "error"):
                    break
            else:
                # No hay evento en cola, esperamos un poco
                await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cancel/{process_id}")
async def cancel_process(process_id: str):
    """
    Marca el proceso como cancelado (y notifica vía SSE).
    """
    state = sse_manager.get_state(process_id)
    
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


@router.get("/download/{process_id}")
async def download_cnc_result(process_id: str, background_tasks: BackgroundTasks):
    """
    Descarga el archivo resultante. Lo borra tras enviarlo.
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
