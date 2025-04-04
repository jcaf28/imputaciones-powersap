# PATH: backend/app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, cnc, imputaciones_ip

SERVICE_NAME = os.environ.get("SERVICE_NAME", "no-service")
BASE_PATH = f"/{SERVICE_NAME}/api"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=BASE_PATH)
app.include_router(cnc.router, prefix=f"{BASE_PATH}/obtencion-cnc", tags=["cnc"])
app.include_router(imputaciones_ip.router, prefix=f"{BASE_PATH}/imputaciones-ip", tags=["imputaciones-ip"])
