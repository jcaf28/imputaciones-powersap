# PATH: backend/app/core/sse_manager.py

import asyncio
from collections import defaultdict, deque

class SSEManager:
    """
    Manejador central de SSE. 
    - Guarda el estado de cada proceso (in-progress, completed, cancelled, error).
    - Mantiene una cola de mensajes para cada proceso (p. ej. deque).
    - Permite a los background tasks "push" mensajes y a la ruta SSE "pop" esos mensajes.
    """

    def __init__(self):
        # Diccionario: process_id -> { status, error, result_file, cancelled, queue }
        self.process_states = {}
        # Podríamos tener un lock si hay alta concurrencia, pero en este ejemplo lo omitimos.

    def start_process(self, process_id: str):
        """Inicia el proceso en 'in-progress' y crea su cola."""
        self.process_states[process_id] = {
            "status": "in-progress",
            "error": None,
            "result_file": None,
            "cancelled": False,
            # Almacenamos los mensajes en una cola para ser consumidos en SSE:
            "queue": deque()
        }

    def send_message(self, process_id: str, message: str):
        """Push de un mensaje (estado intermedio) a la cola SSE."""
        state = self.process_states.get(process_id)
        if state and state["status"] == "in-progress":
            # Añadimos un evento con tipo 'message'
            state["queue"].append(("message", message))

    def mark_completed(self, process_id: str, message: str = "Proceso completado", result_file: str = None):
        """Marca el proceso como completado y notifica por SSE."""
        state = self.process_states.get(process_id)
        if state:
            state["status"] = "completed"
            state["result_file"] = result_file
            # Al notificar completado, lanzamos un evento SSE con tipo 'completed'
            state["queue"].append(("completed", message))

    def mark_cancelled(self, process_id: str, message: str = "Proceso cancelado"):
        """Marca el proceso como cancelado y notifica por SSE."""
        state = self.process_states.get(process_id)
        if state:
            state["status"] = "cancelled"
            state["cancelled"] = True
            state["queue"].append(("cancelled", message))

    def mark_error(self, process_id: str, error_msg: str):
        """Marca el proceso en error y notifica por SSE."""
        state = self.process_states.get(process_id)
        if state:
            state["status"] = "error"
            state["error"] = error_msg
            state["queue"].append(("error", error_msg))

    def get_state(self, process_id: str):
        """Devuelve el dict completo del estado."""
        return self.process_states.get(process_id)

    def pop_next_event(self, process_id: str):
        """
        Extrae el siguiente evento de la cola SSE. 
        Devuelve tupla (event_type, data) o None si no hay mensajes.
        """
        state = self.process_states.get(process_id)
        if not state:
            return None
        queue = state["queue"]
        if queue:
            return queue.popleft()
        return None

    def has_active_process(self, process_id: str) -> bool:
        """Ayuda a saber si existe y está en 'in-progress'."""
        state = self.process_states.get(process_id)
        return state is not None and state["status"] == "in-progress"


# Instancia global de SSEManager
sse_manager = SSEManager()
