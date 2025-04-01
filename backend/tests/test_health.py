# PATH: backend/tests/test_health.py

# /backend/tests/test_health.py

import requests
import time

def test_health_check():
    """Verifica que el endpoint /health responda correctamente."""
    time.sleep(2)  # Pausa breve, por si tarda en arrancar uvicorn

    url = "http://localhost:8000/health"
    response = requests.get(url)
    assert response.status_code == 200, f"Status code inesperado: {response.status_code}"
    assert response.json() == {"status": "ok"}, f"Respuesta inesperada: {response.json()}"
