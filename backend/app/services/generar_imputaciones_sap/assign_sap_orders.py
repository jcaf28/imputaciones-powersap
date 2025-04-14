# PATH: backend/app/services/generar_imputaciones_sap/assign_sap_orders.py

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    Imputaciones, TablaCentral, Extraciclos
)
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
from app.models.models import Imputaciones

# Importamos la nueva lógica de fallback
from app.services.generar_imputaciones_sap.utils._fallback_fuera_sistema import fallback_fuera_sistema

from .utils._assign_sap_orders import (
    obtener_operation_via_db,
    obtener_proyecto_sap,
    obtener_sap_order_id_y_production_order_via_db,
    obtener_sap_order_gg
)

def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    """
    1) Obtiene las imputaciones pendientes.
    2) Para cada imputación:
       - Primero se intenta obtener Operation + OperationActivity
         (vía extraciclos o imp.Tarea).
       - Luego se intenta obtener SAPOrder exacta
         (vía project_dict.ProyectoSap, coincidencia de vértice/unidad).
       - Luego se busca si es indirecto/gg (obtener_sap_order_gg).
       - Si nada coincide => fallback_fuera_sistema(...) con la lógica extendida.
       - Finalmente, inserta la fila en TablaCentral con Cargado_SAP=False.
    """
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

    # Cargamos todos los extraciclos (p.ej. para obtener operation si TareaAsoc)
    extraciclos_all = db.query(Extraciclos).all()

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp_obj = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp_obj:
            logs.append(f"❌ No se encontró la imputación ID={imp_id} en BD.")
            continue

        logs.append(f"🔧 Procesando imputación ID={imp_id}...")

        # 1) Intento rápido por TipoIndirecto + TipoMotivo + opGG
        so_tipo_indirecto = obtener_sap_order_gg(imp_obj, db, logs)
        if so_tipo_indirecto:
            sap_order_id = so_tipo_indirecto.ID
            production_order = so_tipo_indirecto.Order
            operation = so_tipo_indirecto.Operation
            operation_activity = so_tipo_indirecto.OperationActivity
        else:
            # 2) Obtener operation, operationActivity con lógica "extraciclos" o Tarea
            operation, operation_activity = obtener_operation_via_db(
                imp_obj, db, extraciclos_all, logs
            )
            if operation is None or operation_activity is None:
                logs.append(f"❓ No se encontró operación para ID={imp_id}. => fallback.")
                (
                    sap_order_id,
                    production_order,
                    operation,
                    operation_activity
                ) = fallback_fuera_sistema(db, imp_obj, logs)
            else:
                # 3) Intentar coincidencia exacta en SapOrders
                proyecto_sap = obtener_proyecto_sap(imp_obj.Proyecto, db)
                if not proyecto_sap:
                    logs.append(f"❓ ProyectoSap no encontrado => fallback (ID={imp_id}).")
                    (
                        sap_order_id,
                        production_order,
                        operation,
                        operation_activity
                    ) = fallback_fuera_sistema(db, imp_obj, logs)
                else:
                    so_id, so_order = obtener_sap_order_id_y_production_order_via_db(
                        db, proyecto_sap, imp_obj, operation_activity, logs
                    )
                    if so_id is None:
                        logs.append("❌ No se encontró coincidencia exacta => fallback.")
                        (
                            sap_order_id,
                            production_order,
                            operation,
                            operation_activity
                        ) = fallback_fuera_sistema(db, imp_obj, logs)
                    else:
                        sap_order_id = so_id
                        production_order = so_order

        # 4) Insertar en TablaCentral
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
        logs.append(
            f"✅ Imputación {imp_id} insertada en TablaCentral con SapOrder {sap_order_id}."
        )
