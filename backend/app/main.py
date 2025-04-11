# PATH: backend/app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, cnc, imputaciones_ip, tipos_ordenes, cargar_tareas_sap, agregar_imputaciones

ENV = os.getenv("ENVIRONMENT")
SERVICE_NAME = os.getenv("SERVICE_NAME")

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
app.include_router(tipos_ordenes.router, prefix=BASE_PATH, tags=["tipos-ordenes"])
app.include_router(cargar_tareas_sap.router, prefix=f"{BASE_PATH}/cargar-tareas-sap", tags=["cargar-tareas-sap"])
app.include_router(agregar_imputaciones.router, prefix=f"{BASE_PATH}/agregar-imputaciones", tags=["agregar-imputaciones"])