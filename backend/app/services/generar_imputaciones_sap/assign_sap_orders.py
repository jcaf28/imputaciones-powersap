from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, SapOrders, TablaCentral, Areas, Extraciclos, ProjectsDictionary
)
from app.db.session import database_session
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
from app.models.models import Imputaciones

from ._assign_sap_orders import (
    obtener_operation,
    obtener_proyecto_sap,
    obtener_sap_order_id_y_production_order,
    fallback_fuera_sistema
)


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
