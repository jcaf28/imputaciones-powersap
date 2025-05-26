# PATH: backend/app/api/routes/proyectos.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.models import ProjectsDictionary, Imputaciones

router = APIRouter()

# ================== SCHEMAS ==================

class ProyectoCreate(BaseModel):
    ProyectoBaan: str
    ProyectoSap: Optional[str] = None

class ProyectoUpdate(BaseModel):
    ProyectoSap: Optional[str] = None

class ProyectoResponse(BaseModel):
    ProyectoBaan: str
    ProyectoSap: Optional[str]
    imputaciones_count: int = 0  # Para mostrar cuántas imputaciones tiene

    class Config:
        from_attributes = True

# ================== ENDPOINTS ==================

@router.get("/proyectos", response_model=List[ProyectoResponse])
def get_proyectos(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los proyectos con conteo de imputaciones asociadas.
    Permite paginación y búsqueda por ProyectoBaan o ProyectoSap.
    """
    query = db.query(ProjectsDictionary)
    
    # Filtro de búsqueda
    if search:
        query = query.filter(
            (ProjectsDictionary.ProyectoBaan.ilike(f"%{search}%")) |
            (ProjectsDictionary.ProyectoSap.ilike(f"%{search}%"))
        )
    
    proyectos = query.offset(skip).limit(limit).all()
    
    # Añadir conteo de imputaciones para cada proyecto
    result = []
    for proyecto in proyectos:
        imputaciones_count = db.query(Imputaciones).filter(
            Imputaciones.Proyecto == proyecto.ProyectoBaan
        ).count()
        
        result.append(ProyectoResponse(
            ProyectoBaan=proyecto.ProyectoBaan,
            ProyectoSap=proyecto.ProyectoSap,
            imputaciones_count=imputaciones_count
        ))
    
    return result

@router.post("/proyectos", response_model=ProyectoResponse)
def create_proyecto(proyecto: ProyectoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo proyecto.
    """
    try:
        db_proyecto = ProjectsDictionary(
            ProyectoBaan=proyecto.ProyectoBaan,
            ProyectoSap=proyecto.ProyectoSap
        )
        db.add(db_proyecto)
        db.commit()
        db.refresh(db_proyecto)
        
        return ProyectoResponse(
            ProyectoBaan=db_proyecto.ProyectoBaan,
            ProyectoSap=db_proyecto.ProyectoSap,
            imputaciones_count=0
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto '{proyecto.ProyectoBaan}' ya existe"
        )

@router.put("/proyectos/{proyecto_baan}", response_model=ProyectoResponse)
def update_proyecto(
    proyecto_baan: str,
    proyecto_update: ProyectoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un proyecto existente.
    Nota: No se permite cambiar ProyectoBaan (es PK).
    """
    db_proyecto = db.query(ProjectsDictionary).filter(
        ProjectsDictionary.ProyectoBaan == proyecto_baan
    ).first()
    
    if not db_proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Actualizar solo ProyectoSap
    if proyecto_update.ProyectoSap is not None:
        db_proyecto.ProyectoSap = proyecto_update.ProyectoSap
    
    try:
        db.commit()
        db.refresh(db_proyecto)
        
        # Obtener conteo actualizado
        imputaciones_count = db.query(Imputaciones).filter(
            Imputaciones.Proyecto == db_proyecto.ProyectoBaan
        ).count()
        
        return ProyectoResponse(
            ProyectoBaan=db_proyecto.ProyectoBaan,
            ProyectoSap=db_proyecto.ProyectoSap,
            imputaciones_count=imputaciones_count
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al actualizar el proyecto")

@router.delete("/proyectos/{proyecto_baan}")
def delete_proyecto(proyecto_baan: str, db: Session = Depends(get_db)):
    """
    Elimina un proyecto.
    Verifica que no tenga imputaciones asociadas antes de eliminar.
    """
    db_proyecto = db.query(ProjectsDictionary).filter(
        ProjectsDictionary.ProyectoBaan == proyecto_baan
    ).first()
    
    if not db_proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar si tiene imputaciones asociadas
    imputaciones_count = db.query(Imputaciones).filter(
        Imputaciones.Proyecto == proyecto_baan
    ).count()
    
    if imputaciones_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el proyecto. "
                   f"Tiene {imputaciones_count} imputación(es) asociada(s)"
        )
    
    try:
        db.delete(db_proyecto)
        db.commit()
        return {"message": f"Proyecto '{proyecto_baan}' eliminado correctamente"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al eliminar el proyecto")

@router.get("/proyectos/{proyecto_baan}", response_model=ProyectoResponse)
def get_proyecto(proyecto_baan: str, db: Session = Depends(get_db)):
    """
    Obtiene un proyecto específico por su ProyectoBaan.
    """
    db_proyecto = db.query(ProjectsDictionary).filter(
        ProjectsDictionary.ProyectoBaan == proyecto_baan
    ).first()
    
    if not db_proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    imputaciones_count = db.query(Imputaciones).filter(
        Imputaciones.Proyecto == proyecto_baan
    ).count()
    
    return ProyectoResponse(
        ProyectoBaan=db_proyecto.ProyectoBaan,
        ProyectoSap=db_proyecto.ProyectoSap,
        imputaciones_count=imputaciones_count
    )