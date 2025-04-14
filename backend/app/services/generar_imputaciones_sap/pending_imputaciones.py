# PATH: backend/app/services/generar_imputaciones_sap/pending_imputaciones.py

from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from app.models.models import Imputaciones, TablaCentral

def get_imputaciones_pendientes_count(db: Session) -> int:
    return db.query(Imputaciones).outerjoin(TablaCentral).filter(
        or_(
            TablaCentral.ID == None,
            TablaCentral.Cargado_SAP == False
        )
    ).count()

def get_imputaciones_pendientes(db: Session):
    """
    Devuelve las imputaciones que no tienen entrada en Tabla_Central o las que tienen Cargado_SAP = False.
    """
    results = db.query(Imputaciones).outerjoin(TablaCentral).filter(
        or_(
            TablaCentral.ID == None,
            TablaCentral.Cargado_SAP == False
        )
    ).all()

    imputaciones_list = []
    for imp in results:
        imputaciones_list.append({
            "id": imp.ID,
            "fechaImp": imp.FechaImp,
            "codEmpleado": imp.CodEmpleado,
            "timpu": imp.Timpu,
            "horas": imp.Horas,
            "proyecto": imp.Proyecto,
            "tipoCoche": imp.TipoCoche,
            "numCoche": imp.NumCoche,
            "centroTrabajo": imp.CentroTrabajo,
            "tarea": imp.Tarea,
            "tareaAsoc": imp.TareaAsoc,
            "tipoIndirecto": imp.TipoIndirecto,
            "tipoMotivo": imp.TipoMotivo,
            "timestampInput": imp.TimestampInput,
            "tipoImput": imp.TipoImput,
            "areaTarea": imp.AreaTarea,
            "area_id": imp.area_id,
        })

    return imputaciones_list
