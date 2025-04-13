# PATH: backend/app/api/routes/fake_generar_imputaciones_sap.py

"""
Mockup backend con FastAPI que simula el flujo SSE para "Generar Imputaciones SAP".

1) GET  /generar-imputaciones-sap/list
2) POST /generar-imputaciones-sap/start -> { process_id }
3) GET  /generar-imputaciones-sap/events/{process_id}  (SSE)
4) POST /generar-imputaciones-sap/cancel/{process_id}
5) GET  /generar-imputaciones-sap/download/{process_id} -> CSV
"""

import time
import uuid
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response

app = FastAPI()

# =====================================================================
# Datos Fake: Imputaciones pendientes
# =====================================================================
FAKE_DATA = [
    {
        "id": 1,
        "fechaImp": "2025-04-01",
        "codEmpleado": "E123",
        "horas": 5.5,
        "proyecto": "P001",
        "tipoCoche": "A",
        "cargadoSap": False
    },
    {
        "id": 2,
        "fechaImp": "2025-04-02",
        "codEmpleado": "E124",
        "horas": 3.75,
        "proyecto": "P002",
        "tipoCoche": "C",
        "cargadoSap": False
    },
    {
        "id": 3,
        "fechaImp": "2025-04-05",
        "codEmpleado": "E555",
        "horas": 2.0,
        "proyecto": "P003",
        "tipoCoche": "B",
        "cargadoSap": False
    }
]

# =====================================================================
# Estructuras en memoria: SESSIONS (logs, status, csv_data)
# =====================================================================
SESSIONS: Dict[str, Dict[str, Any]] = {}
# Ejemplo:
# SESSIONS[process_id] = {
#   "status": "in-progress" | "completed" | "cancelled" | "error",
#   "logs": [...],
#   "csv_data": bytes
# }


# =====================================================================
# 1) GET /generar-imputaciones-sap/list
# =====================================================================
@app.get("/generar-imputaciones-sap/list")
def get_imputaciones_pendientes() -> List[Dict[str, Any]]:
    """
    Devuelve imputaciones (FAKE_DATA) que simulan "no en TablaCentral o CargadoSap=0"
    """
    return FAKE_DATA


# =====================================================================
# 2) POST /generar-imputaciones-sap/start
# =====================================================================
@app.post("/generar-imputaciones-sap/start")
def start_generar_sap(background_tasks: BackgroundTasks):
    """
    Inicia un proceso SSE simulado. Devuelve { process_id }.
    """
    process_id = str(uuid.uuid4())

    # Inicializamos la sesión
    SESSIONS[process_id] = {
        "status": "in-progress",
        "logs": ["Proceso iniciado."],
        "csv_data": b""
    }

    # Lanza una tarea en background que generará logs y creará el CSV
    background_tasks.add_task(fake_sap_long_task, process_id)

    return {"process_id": process_id}


# ---------------------------------------------------------------------
def fake_sap_long_task(process_id: str):
    """
    Simula un proceso largo que va añadiendo logs, 
    y finalmente crea un CSV 'en memoria'.
    """
    try:
        time.sleep(1.5)
        add_log(process_id, "Cargando imputaciones pendientes...")

        time.sleep(2)
        add_log(process_id, f"Encontradas {len(FAKE_DATA)} imputaciones pendientes.")

        time.sleep(2)
        add_log(process_id, "Generando CSV en memoria...")

        # Simulamos la creación de un CSV
        csv_header = "ID,FechaImp,Empleado,Horas,Proyecto,TipoCoche,CargadoSap\n"
        csv_rows = []
        for row in FAKE_DATA:
            csv_rows.append(
                f"{row['id']},{row['fechaImp']},{row['codEmpleado']},{row['horas']},{row['proyecto']},{row['tipoCoche']},{row['cargadoSap']}\n"
            )
        csv_content = csv_header + "".join(csv_rows)
        SESSIONS[process_id]["csv_data"] = csv_content.encode("utf-8")

        time.sleep(2)
        add_log(process_id, "¡Proceso completado con éxito!")
        mark_completed(process_id, "CSV listo para descargar.")
    except Exception as e:
        mark_error(process_id, f"Error inesperado: {str(e)}")


def add_log(process_id: str, message: str):
    session = SESSIONS.get(process_id)
    if session and session["status"] == "in-progress":
        session["logs"].append(message)


def mark_completed(process_id: str, message: str):
    session = SESSIONS.get(process_id)
    if session and session["status"] == "in-progress":
        session["logs"].append(message)
        session["status"] = "completed"


def mark_error(process_id: str, message: str):
    session = SESSIONS.get(process_id)
    if session and session["status"] not in ["completed", "cancelled"]:
        session["logs"].append(message)
        session["status"] = "error"


# =====================================================================
# 3) GET /generar-imputaciones-sap/events/{process_id}  -> SSE
# =====================================================================
@app.get("/generar-imputaciones-sap/events/{process_id}")
async def sse_events(request: Request, process_id: str):
    """
    SSE: Envío de logs en tiempo real.
    - Polling cada 0.4s para ver si hay logs nuevos.
    - Corta cuando se complete, cancele o haya error.
    """
    if process_id not in SESSIONS:
        raise HTTPException(404, detail="process_id no encontrado")

    # Llevaremos un índice de qué logs ya se han enviado al cliente
    last_index_sent = 0

    async def event_generator():
        nonlocal last_index_sent

        while True:
            # Si el cliente se desconecta, paramos
            if await request.is_disconnected():
                break

            session = SESSIONS.get(process_id)
            if not session:
                break  # Se borró?

            current_status = session["status"]
            logs_list = session["logs"]

            # Enviamos logs nuevos
            while last_index_sent < len(logs_list):
                msg = logs_list[last_index_sent]
                last_index_sent += 1

                # Formato SSE
                yield "event: message\n"
                yield f"data: {msg}\n\n"

            # Si estado final, mandamos event final
            if current_status in ["completed", "cancelled", "error"]:
                yield f"event: {current_status}\n"
                yield f"data: {session['logs'][-1] if session['logs'] else ''}\n\n"
                break

            # Espera un poco
            await time.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# =====================================================================
# 4) POST /generar-imputaciones-sap/cancel/{process_id}
# =====================================================================
@app.post("/generar-imputaciones-sap/cancel/{process_id}")
def cancel_generar_sap(process_id: str):
    session = SESSIONS.get(process_id)
    if not session:
        return {"message": "process_id no encontrado"}

    if session["status"] == "in-progress":
        session["status"] = "cancelled"
        session["logs"].append("Proceso cancelado.")
        return {"message": "Proceso cancelado."}
    else:
        return {"message": f"El proceso está en estado: {session['status']}"}


# =====================================================================
# 5) GET /generar-imputaciones-sap/download/{process_id}
# =====================================================================
@app.get("/generar-imputaciones-sap/download/{process_id}")
def download_csv(process_id: str):
    session = SESSIONS.get(process_id)
    if not session:
        raise HTTPException(404, detail="process_id no encontrado")

    if session["status"] != "completed":
        raise HTTPException(400, detail=f"Proceso no completado. Estado: {session['status']}")

    csv_data = session["csv_data"]
    if not csv_data:
        raise HTTPException(400, detail="No hay CSV disponible")

    return Response(content=csv_data, media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="imputaciones_sap_{process_id}.csv"'
    })
