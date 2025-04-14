
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, SapOrders, Areas, Extraciclos, ProjectsDictionary
)

from app.models.models import Imputaciones

# -------------------------------------------------------------------------------------
# FUNCIONES DE TRADUCCIÓN (copiadas tal cual, con leves retoques de import)
# -------------------------------------------------------------------------------------
def obtener_operation(imp: Imputaciones, sap_orders: List[SapOrders], extraciclos: List[Extraciclos], db: Session):
    """
    Lógica EXACTA que pasaste:
    1) Si TareaAsoc no es nulo => buscar en Extraciclos
    2) Si TipoMotivo/TipoIndirecto => buscar OpGG en Areas + filtrar en sap_orders
    3) Sino => si sap_order.Operation == imp.Tarea
    """
    if imp.TareaAsoc:
        # Usar imp.AreaTarea para obtener la entrada correspondiente de Extraciclos
        extraciclo_correspondiente = next((c for c in extraciclos if c.AreaTarea == imp.AreaTarea), None)
        if extraciclo_correspondiente and extraciclo_correspondiente.OASAP:
            oasap_partes = extraciclo_correspondiente.OASAP.split('-')
            return oasap_partes[0], extraciclo_correspondiente.OASAP

    elif imp.TipoMotivo is not None and imp.TipoIndirecto is not None:
        # Obtener el registro de Areas relacionado
        area_relacionada = db.query(Areas).filter(Areas.CentroTrabajo == imp.CentroTrabajo).first()
        opgg = area_relacionada.OpGG if area_relacionada else None

        # Buscar en sap_orders donde .TipoIndirecto == imp.TipoIndirecto, etc.
        sap_order_coincidente = None
        for so in sap_orders:
            if (so.TipoIndirecto == imp.TipoIndirecto and
                so.TipoMotivo == imp.TipoMotivo and
                so.Operation == opgg and
                so.ActiveOrder):
                sap_order_coincidente = so
                break

        if sap_order_coincidente:
            return sap_order_coincidente.Operation, sap_order_coincidente.OperationActivity

    # Si TareaAsoc es nulo => filtrar sap_orders donde so.Operation == imp.Tarea
    for so in sap_orders:
        if so.Operation == imp.Tarea:
            return so.Operation, so.OperationActivity

    return None, None

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
def obtener_sap_order_id_y_production_order(
    proyecto_sap: str,
    imp: Imputaciones,
    operation: str,
    operation_activity: str,
    sap_orders: List[SapOrders],
    db: Session,
    logs: List[str]
):
    """
    Criterio real:
      - ActiveOrder=1
      - so.Project == proyecto_sap
      - so.Vertice == imp.TipoCoche
      - so.CarNumber == imp.NumCoche
      - so.Operation == operation
      - so.OperationActivity == operation_activity
    Si hay varias => la de mayor so.TimestampInput
    Si 0 => None, None
    """
    coincidencias = []
    for so in sap_orders:
        if (so.ActiveOrder and
            str(so.Project) == str(proyecto_sap) and
            str(so.Vertice) == str(imp.TipoCoche) and
            str(so.CarNumber) == str(imp.NumCoche) and
            str(so.Operation) == str(operation) and
            str(so.OperationActivity) == str(operation_activity)
        ):
            coincidencias.append(so)

    if not coincidencias:
        return None, None

    # Escogemos la de mayor TimestampInput
    chosen = max(coincidencias, key=lambda x: x.TimestampInput or 0)

    # (Opcional) Si hay más de 1, registrar duplicado en log
    if len(coincidencias) > 1:
        logs.append(f"⚠️ Duplicado: {len(coincidencias)} coincidencias => se elige {chosen.ID} (TimestampInput más reciente).")

    return chosen.ID, chosen.Order


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

