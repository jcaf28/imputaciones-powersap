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
    Lógica EXACTA, sin cargar sap_orders en memoria.
    1) Si TareaAsoc => buscar extraciclos
    2) Si TipoMotivo/TipoIndirecto => 
       - obtener area -> opGG
       - query sap_orders donde TipoIndirecto, TipoMotivo, Operation=opGG, ActiveOrder=1
         -> si se halla => return (Operation, OperationActivity)
    3) Else => filtrar sap_orders donde Operation == imp.Tarea
    Retorna (operation, operationActivity) o (None, None).
    """

    # -------------------------------------------
    # 1) TareaAsoc => ver extraciclos
    # -------------------------------------------
    if imp.TareaAsoc:
        extraciclo_correspondiente = next(
            (c for c in extraciclos if c.AreaTarea == imp.AreaTarea), None
        )
        if extraciclo_correspondiente and extraciclo_correspondiente.OASAP:
            # "OASAP" es 'XYZ-123' => parted en [0], [1]
            partes = extraciclo_correspondiente.OASAP.split('-')
            return (partes[0], extraciclo_correspondiente.OASAP)

    # -------------------------------------------
    # 2) Si TipoMotivo/TipoIndirecto => opGG
    # -------------------------------------------
    if imp.TipoMotivo is not None and imp.TipoIndirecto is not None:
        area_relacionada = db.query(Areas).filter(
            Areas.CentroTrabajo == imp.CentroTrabajo
        ).first()
        opgg = area_relacionada.OpGG if area_relacionada else None

        if opgg:
            # Query a SapOrders
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
                return (so.Operation, so.OperationActivity)

    # -------------------------------------------
    # 3) Caso final => TareaAsoc nulo, Tarea => Operation
    #    Buscamos SapOrders donde Operation == imp.Tarea, Active=1
    # -------------------------------------------
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

    # Nada
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

