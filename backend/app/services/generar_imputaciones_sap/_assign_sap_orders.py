# PATH: backend/app/services/generar_imputaciones_sap/_assign_sap_orders.py

from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, SapOrders, Areas, Extraciclos, ProjectsDictionary
)

from app.models.models import Imputaciones

# -------------------------------------------------------------------------------------
# FUNCIONES DE TRADUCCIÓN (copiadas tal cual, con leves retoques de import)
# -------------------------------------------------------------------------------------
def obtener_operation_via_db(
    imp: Imputaciones,
    db: Session,
    extraciclos: List[Extraciclos],
    logs: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    1) Si TareaAsoc => buscar extraciclos
    2) Else => buscar por imp.Tarea
    """
    # 1) TareaAsoc => ver extraciclos
    if imp.TareaAsoc:
        extraciclo_correspondiente = next(
            (c for c in extraciclos if c.AreaTarea == imp.AreaTarea), None
        )
        if extraciclo_correspondiente and extraciclo_correspondiente.OASAP:
            partes = extraciclo_correspondiente.OASAP.split('-')
            return (partes[0], extraciclo_correspondiente.OASAP)

    # 2) Buscar por imp.Tarea directamente
    so2 = (
        db.query(SapOrders)
        .filter(
            SapOrders.ActiveOrder == True,
            SapOrders.Operation == imp.Tarea
        )
        .order_by(desc(SapOrders.TimestampInput))
        .first()
    )
    if so2:
        return (so2.Operation, so2.OperationActivity)

    return (None, None)


def obtener_proyecto_sap(proyecto_baan: str, db: Session) -> str:
    """
    Retorna el ProyectoSap correspondiente, si existe.
    """
    project_dict_entry = db.query(ProjectsDictionary).filter(
        ProjectsDictionary.ProyectoBaan == proyecto_baan
    ).first()
    return project_dict_entry.ProyectoSap if project_dict_entry else None

# -------------------------------------------------------------------------------------
# OBTENER SAP_ORDER => con coincidencias EXACTAS y picking la de mayor TimestampInput
# -------------------------------------------------------------------------------------
def obtener_sap_order_id_y_production_order_via_db(
    db: Session,
    proyecto_sap: str,
    imp: Imputaciones,
    operation_activity: str,
    logs: List[str]
):
    coincidencia = (
        db.query(SapOrders)
        .filter(
            SapOrders.ActiveOrder == True,
            SapOrders.Project == proyecto_sap,
            SapOrders.Vertice == imp.TipoCoche,
            SapOrders.CarNumber == imp.NumCoche,
            SapOrders.OperationActivity == operation_activity
        )
        .order_by(desc(SapOrders.TimestampInput))
        .first()
    )

    if coincidencia:
        return coincidencia.ID, coincidencia.Order
    else:
        return None, None

def obtener_sap_order_gg(
    imp: Imputaciones,
    db: Session,
    logs: List[str]
) -> Optional[SapOrders]:
    """
    Devuelve la SapOrder coincidente si hay TipoMotivo + TipoIndirecto
    y la Operation esperada desde Areas (OpGG), sin ceros a la izquierda.
    """
    if imp.TipoMotivo and imp.TipoIndirecto:
        area_relacionada = db.query(Areas).filter(
            Areas.CentroTrabajo == imp.CentroTrabajo
        ).first()

        opgg = area_relacionada.OpGG if area_relacionada and area_relacionada.OpGG else None

        if opgg:
            so = (
                db.query(SapOrders)
                .filter(
                    SapOrders.ActiveOrder == True,
                    SapOrders.TipoIndirecto == imp.TipoIndirecto,
                    SapOrders.TipoMotivo == imp.TipoMotivo,
                    SapOrders.Operation == opgg
                )
                .order_by(desc(SapOrders.TimestampInput))
                .first()
            )
            if so:
                logs.append(f"✅ Coincidencia por TipoIndirecto/Motivo con Operation='{opgg}' encontrada.")
                return so

    return None


def fallback_fuera_sistema(db: Session, logs: List[str]) -> int:
    """
    Busca la SapOrder con Operation='FUERA_SISTEMA' y ActiveOrder=1.
    Devuelve su ID, o None si no existe.
    """
    so = db.query(SapOrders).filter(
        SapOrders.ActiveOrder == True,
        SapOrders.Operation == "FUERA_SISTEMA"
    ).order_by(desc(SapOrders.TimestampInput)).first()

    if so:
        return so.ID
    logs.append("⚠️ No se encontró la SapOrder genérica FUERA_SISTEMA.")
    return None

