from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import TiposOrdenes

router = APIRouter()

@router.get("/tipos-ordenes")
def get_tipos_ordenes(db: Session = Depends(get_db)):
  registros = db.query(TiposOrdenes).all()
  return registros
