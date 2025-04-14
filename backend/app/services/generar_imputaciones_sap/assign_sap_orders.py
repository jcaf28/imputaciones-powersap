# PATH: backend/app/services/generar_imputaciones_sap/assign_sap_orders.py

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
    obtener_operation_via_db,
    obtener_proyecto_sap,
    obtener_sap_order_id_y_production_order_via_db,
    fallback_fuera_sistema,
    obtener_sap_order_gg
)


# -------------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: asigna imputaciones a SAPOrders y crea filas en Tabla_Central
# -------------------------------------------------------------------------------------
def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    """
    1) Obtiene las imputaciones pendientes.
    2) Para cada imputación:
        - Aplica obtener_operation(...) + obtener_proyecto_sap(...) 
        - Crea la coincidencia con lógica SQL (via obtener_sap_order_id_y_production_order_via_db) 
          => si no hay => fallback_fuera_sistema
        - Inserta en TablaCentral con Cargado_SAP=0
    3) Al final, logs[] explica todo el proceso (SSE).
    """
    # Limpiar previamente las imputaciones no cargadas en Tabla_Central
    logs.append("🧹 Eliminando imputaciones previas con Cargado_SAP = False en Tabla_Central...")
    deleted_rows = db.query(TablaCentral).filter(TablaCentral.Cargado_SAP == False).delete()
    db.commit()
    logs.append(f"🗑️ {deleted_rows} filas eliminadas de Tabla_Central.")

    logs.append("🔎 Buscando imputaciones pendientes en BD...")
    imps_pendientes = get_imputaciones_pendientes(db)

    if not imps_pendientes:
        logs.append("No hay imputaciones pendientes.")
        return

    logs.append(f"Encontradas {len(imps_pendientes)} imputaciones pendientes.")

    # Pre-cargar extraciclos (sí tiene sentido)
    extraciclos_all = db.query(Extraciclos).all()

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp_obj = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp_obj:
            logs.append(f"❌ No se encontró la imputación ID={imp_id} en BD.")
            continue

        logs.append(f"🔧 Procesando imputación ID={imp_id}...")

        # 1) Intento por TipoIndirecto + TipoMotivo + opGG
        so_tipo_indirecto = obtener_sap_order_gg(imp_obj, db, logs)
        if so_tipo_indirecto:
            sap_order_id = so_tipo_indirecto.ID
            production_order = so_tipo_indirecto.Order
            operation = so_tipo_indirecto.Operation
            operation_activity = so_tipo_indirecto.OperationActivity

        else:
            # 2) Obtener operation, operationActivity con lógica clásica
            operation, operation_activity = obtener_operation_via_db(imp_obj, db, extraciclos_all, logs)
            if operation is None or operation_activity is None:
                logs.append(f"❓ No se encontró operación para ID={imp_id}. => fallback.")
                sap_order_id = fallback_fuera_sistema(db, logs)
                production_order = None
            else:
                proyecto_sap = obtener_proyecto_sap(imp_obj.Proyecto, db)
                if not proyecto_sap:
                    logs.append(f"❓ ProyectoSap no encontrado => fallback. ID={imp_id}.")
                    sap_order_id = fallback_fuera_sistema(db, logs)
                    production_order = None
                else:
                    so_id, so_order = obtener_sap_order_id_y_production_order_via_db(
                        db, proyecto_sap, imp_obj, operation_activity, logs
                    )
                    if so_id is None:
                        logs.append(f"❌ No se encontró coincidencia exacta => fallback.")
                        sap_order_id = fallback_fuera_sistema(db, logs)
                        production_order = None
                    else:
                        sap_order_id = so_id
                        production_order = so_order

        # 4) Insertar en Tabla_Central
        new_row = TablaCentral(
            imputacion_id=imp_id,
            sap_order_id=sap_order_id,
            Employee_Number=imp_obj.CodEmpleado,
            Date=imp_obj.FechaImp,
            HourType="Production Direct Hour",
            ProductionOrder=production_order,
            Operation=operation,
            OperationActivity=operation_activity,
            Hours=imp_obj.Horas,
            Cargado_SAP=False
        )
        db.add(new_row)
        db.commit()
        logs.append(f"✅ Imputación {imp_id} insertada en TablaCentral con SapOrder {sap_order_id}.")