from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, SapOrders, TablaCentral, Areas, Extraciclos, ProjectsDictionary
)
from app.db.session import database_session
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
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


# -------------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: asigna imputaciones a SAPOrders y crea filas en Tabla_Central
# -------------------------------------------------------------------------------------
def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    """
    1) Obtiene las imputaciones pendientes.
    2) Para cada imputación:
        - Aplica obtener_operation(...) + obtener_proyecto_sap(...) 
        - Crea la coincidencia con obtener_sap_order_id_y_production_order(...) 
          => si no hay => fallback_fuera_sistema
        - Inserta en TablaCentral con Cargado_SAP=0
    3) Al final, logs[] explica todo el proceso (SSE).
    """
    from app.models.models import TablaCentral, Imputaciones

    # Limpiar previamente las imputaciones no cargadas en Tabla_Central
    logs.append("🧹 Eliminando imputaciones previas con Cargado_SAP = False en Tabla_Central...")
    deleted_rows = db.query(TablaCentral).filter(TablaCentral.Cargado_SAP == False).delete()
    db.commit()
    logs.append(f"🗑️ {deleted_rows} filas eliminadas de Tabla_Central.")


    logs.append("🔎 Buscando imputaciones pendientes en BD...")
    imps_pendientes = get_imputaciones_pendientes(db)  # devuelves dicts con id, etc.

    if not imps_pendientes:
        logs.append("No hay imputaciones pendientes.")
        return

    logs.append(f"Encontradas {len(imps_pendientes)} imputaciones pendientes.")

    # Pre-cargamos sap_orders y extraciclos, para no query en bucle
    sap_orders_all = db.query(SapOrders).all()
    extraciclos_all = db.query(Extraciclos).all()

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp_obj = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp_obj:
            logs.append(f"❌ No se encontró la imputación ID={imp_id} en BD.")
            continue

        logs.append(f"Procesando imputación ID={imp_id}...")

        # 1) Obtener operation, operationActivity
        operation, operation_activity = obtener_operation(imp_obj, sap_orders_all, extraciclos_all, db)
        if operation is None or operation_activity is None:
            logs.append(f"❓ No se encontró operation para ID={imp_id}. => fallback.")
            sap_order_id = fallback_fuera_sistema(db, logs)
            production_order = None
        else:
            # 2) proyecto_sap
            proyecto_sap = obtener_proyecto_sap(imp_obj.Proyecto, db)
            if not proyecto_sap:
                logs.append(f"❓ ProyectoSap no encontrado => fallback. ID={imp_id}.")
                sap_order_id = fallback_fuera_sistema(db, logs)
                production_order = None
            else:
                # 3) obtener sap_order real
                so_id, so_order = obtener_sap_order_id_y_production_order(
                    proyecto_sap, imp_obj, operation, operation_activity, 
                    sap_orders_all, db, logs
                )
                if so_id is None:
                    # fallback
                    sap_order_id = fallback_fuera_sistema(db, logs)
                    production_order = None
                else:
                    sap_order_id = so_id
                    production_order = so_order

        # 4) Insertar en Tabla_Central con Cargado_SAP=False
        new_row = TablaCentral(
            imputacion_id = imp_id,
            sap_order_id = sap_order_id,
            Employee_Number = imp_obj.CodEmpleado,
            Date = imp_obj.FechaImp,
            HourType = "Production Direct Hour",  # (o la que quieras)
            ProductionOrder = production_order,
            Operation = operation,
            OperationActivity = operation_activity,
            Hours = imp_obj.Horas,
            Cargado_SAP = False
        )
        db.add(new_row)
        db.commit()

        logs.append(f"📝 Imputacion {imp_id} => TablaCentral, Cargado_SAP=0. (sap_order_id={sap_order_id})")

    logs.append("🏁 Finalizada la asignación. Revisa TablaCentral para ver las filas nuevas.")
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, SapOrders, TablaCentral, Areas, Extraciclos, ProjectsDictionary
)
from app.db.session import database_session
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
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


# -------------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: asigna imputaciones a SAPOrders y crea filas en Tabla_Central
# -------------------------------------------------------------------------------------
def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    """
    1) Obtiene las imputaciones pendientes.
    2) Para cada imputación:
        - Aplica obtener_operation(...) + obtener_proyecto_sap(...) 
        - Crea la coincidencia con obtener_sap_order_id_y_production_order(...) 
          => si no hay => fallback_fuera_sistema
        - Inserta en TablaCentral con Cargado_SAP=0
    3) Al final, logs[] explica todo el proceso (SSE).
    """
    from app.models.models import TablaCentral, Imputaciones

    logs.append("🔎 Buscando imputaciones pendientes en BD...")
    imps_pendientes = get_imputaciones_pendientes(db)  # devuelves dicts con id, etc.

    if not imps_pendientes:
        logs.append("No hay imputaciones pendientes.")
        return

    logs.append(f"Encontradas {len(imps_pendientes)} imputaciones pendientes.")

    # Pre-cargamos sap_orders y extraciclos, para no query en bucle
    sap_orders_all = db.query(SapOrders).all()
    extraciclos_all = db.query(Extraciclos).all()

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp_obj = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp_obj:
            logs.append(f"❌ No se encontró la imputación ID={imp_id} en BD.")
            continue

        logs.append(f"Procesando imputación ID={imp_id}...")

        # 1) Obtener operation, operationActivity
        operation, operation_activity = obtener_operation(imp_obj, sap_orders_all, extraciclos_all, db)
        if operation is None or operation_activity is None:
            logs.append(f"❓ No se encontró operation para ID={imp_id}. => fallback.")
            sap_order_id = fallback_fuera_sistema(db, logs)
            production_order = None
        else:
            # 2) proyecto_sap
            proyecto_sap = obtener_proyecto_sap(imp_obj.Proyecto, db)
            if not proyecto_sap:
                logs.append(f"❓ ProyectoSap no encontrado => fallback. ID={imp_id}.")
                sap_order_id = fallback_fuera_sistema(db, logs)
                production_order = None
            else:
                # 3) obtener sap_order real
                so_id, so_order = obtener_sap_order_id_y_production_order(
                    proyecto_sap, imp_obj, operation, operation_activity, 
                    sap_orders_all, db, logs
                )
                if so_id is None:
                    # fallback
                    sap_order_id = fallback_fuera_sistema(db, logs)
                    production_order = None
                else:
                    sap_order_id = so_id
                    production_order = so_order

        # 4) Insertar en Tabla_Central con Cargado_SAP=False
        new_row = TablaCentral(
            imputacion_id = imp_id,
            sap_order_id = sap_order_id,
            Employee_Number = imp_obj.CodEmpleado,
            Date = imp_obj.FechaImp,
            HourType = "Production Direct Hour",  # (o la que quieras)
            ProductionOrder = production_order,
            Operation = operation,
            OperationActivity = operation_activity,
            Hours = imp_obj.Horas,
            Cargado_SAP = False
        )
        db.add(new_row)
        db.commit()

        logs.append(f"📝 Imputacion {imp_id} => TablaCentral, Cargado_SAP=0. (sap_order_id={sap_order_id})")

    logs.append("🏁 Finalizada la asignación. Revisa TablaCentral para ver las filas nuevas.")
