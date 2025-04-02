# PATH: backend/app/api/routes/imputaciones_ip.py

from fastapi import APIRouter, Request, UploadFile, BackgroundTasks, Query, HTTPException, File
from fastapi.responses import StreamingResponse, FileResponse
import uuid
import os
import asyncio

from app.core.sse_manager import sse_manager
from app.services.validation_imputaciones_service import validate_imputaciones_file
from app.services.imputaciones_ip_processor import long_running_task 

router = APIRouter()

FILE_TYPES = {
    0: "wbs_por_clave",
    1: "listado_usuarios",
    2: "descarga_imputaciones",
    3: "fichajes_sap"
}

@router.post("/validate-file")
async def validate_file(index: int = Query(...), file: UploadFile = File(...)):
    """
    Endpoint real de validación: guardamos el archivo en /tmp, 
    usamos 'validate_imputaciones_file' para chequear columnas mínimas,
    y si OK, respondemos 200.
    """
    if index not in FILE_TYPES:
        raise HTTPException(status_code=400, detail="Índice de archivo no válido")

    file_type = FILE_TYPES[index]
    if not file:
        raise HTTPException(status_code=400, detail="Se requiere un archivo")

    # Guardar temporalmente
    tmp_path = f"/tmp/validate_{uuid.uuid4()}_{file.filename}"
    with open(tmp_path, "wb") as f_out:
        content = await file.read()
        f_out.write(content)

    # Llamar a la validación
    try:
        validate_imputaciones_file(tmp_path, file_type)
    except ValueError as e:
        # Lanza HTTP 400 si hay error en validación
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # (Opcional) Podrías borrar el archivo o dejarlo
        pass

    return {"message": f"El archivo '{file_type}' es válido"}


@router.post("/start")
async def start_imputaciones_process(
    file1: UploadFile,
    file2: UploadFile,
    file3: UploadFile,
    file4: UploadFile,
    background_tasks: BackgroundTasks
):
    process_id = str(uuid.uuid4())
    tmp_dir = "/tmp"

    # Guardar los 4 ficheros
    file_paths = []
    for i, f in enumerate([file1, file2, file3, file4], start=1):
        file_path = os.path.join(tmp_dir, f"{process_id}_file{i}_{f.filename}")
        with open(file_path, "wb") as dest:
            content = await f.read()
            dest.write(content)
        file_paths.append(file_path)

    # Iniciamos SSE
    sse_manager.start_process(process_id)

    # Invoca la ETL real, en vez del 'long_running_fake'
    background_tasks.add_task(long_running_task, process_id, file_paths)

    return {"process_id": process_id}


@router.get("/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    Enviamos eventos SSE al frontend hasta que el proceso termine, se cancele o haya error.
    Igual que en cnc.py
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
    Marca el proceso como cancelado (y notifica vía SSE).
    """
    state = sse_manager.get_state(process_id)
    if state:
        sse_manager.mark_cancelled(process_id)
        return {"message": "Proceso cancelado"}
    return {"message": "Proceso no encontrado"}


@router.get("/download/{process_id}")
async def download_imputaciones_result(process_id: str, background_tasks: BackgroundTasks):
    """
    Descarga el archivo resultante (fake). Lo borra tras enviarlo.
    """
    state = sse_manager.get_state(process_id)
    if not state:
        return {"error": "Process ID no encontrado"}

    if state["status"] != "completed":
        return {"error": f"No está completado (status = {state['status']})"}

    result_file = state.get("result_file")
    if not result_file or not os.path.exists(result_file):
        return {"error": "No se encontró el archivo resultante"}

    # Borrar el archivo tras enviarlo
    background_tasks.add_task(os.remove, result_file)

    return FileResponse(
        path=result_file,
        filename=os.path.basename(result_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=background_tasks
    )
