# PATH: backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, cnc, imputaciones_ip  

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(health.router, prefix="/ip/api")
app.include_router(cnc.router, prefix="/ip/api/obtencion-cnc", tags=["cnc"])
app.include_router(imputaciones_ip.router, prefix="/ip/api/imputaciones-ip", tags=["imputaciones-ip"])
