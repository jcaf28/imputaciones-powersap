# PATH: backend/app/services/generar_imputaciones_sap/assign_sap_orders.py

from typing import List
from sqlalchemy.orm import Session
from app.models.models import (
    Imputaciones, TablaCentral, Extraciclos
)
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
from app.services.generar_imputaciones_sap.utils._fallback_fuera_sistema import fallback_fuera_sistema
from .utils._assign_sap_orders import (
    obtener_operation_via_db,
    obtener_proyecto_sap,
    obtener_sap_order_id_y_production_order_via_db,
    obtener_sap_order_gg
)

def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    logs.append("🧹 Eliminando imputaciones previas con Cargado_SAP=False en Tabla_Central...")
    deleted = db.query(TablaCentral).filter(TablaCentral.Cargado_SAP == False).delete()
    db.commit()
    logs.append(f"🗑️ {deleted} filas eliminadas de Tabla_Central.")

    logs.append("🔎 Buscando imputaciones pendientes en BD...")
    imps_pendientes = get_imputaciones_pendientes(db)
    if not imps_pendientes:
        logs.append("No hay imputaciones pendientes.")
        return

    logs.append(f"Encontradas {len(imps_pendientes)} imputaciones pendientes.")
    extraciclos_all = db.query(Extraciclos).all()

    for imp_dict in imps_pendientes:
        imp_id = imp_dict["id"]
        imp = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp:
            logs.append(f"❌ Imputación ID={imp_id} no se encontró en BD.")
            continue

        logs.append(f"🔧 Procesando imputación ID={imp_id}...")

        so_indirecto = obtener_sap_order_gg(imp, db, logs)
        if so_indirecto:
            sap_id = so_indirecto.ID
            prod_order = so_indirecto.Order
            op = so_indirecto.Operation
            op_act = so_indirecto.OperationActivity
        else:
            op, op_act = obtener_operation_via_db(imp, db, extraciclos_all, logs)
            if op is None or op_act is None:
                logs.append(f"❓ Sin operation => fallback para ID={imp_id}.")
                (sap_id, prod_order, op, op_act) = fallback_fuera_sistema(db, imp, logs)
            else:
                proyecto_sap = obtener_proyecto_sap(imp.Proyecto, db)
                if not proyecto_sap:
                    logs.append(f"❓ ProyectoSap no encontrado => fallback (ID={imp_id}).")
                    (sap_id, prod_order, op, op_act) = fallback_fuera_sistema(db, imp, logs)
                else:
                    so_id, so_order = obtener_sap_order_id_y_production_order_via_db(
                        db, proyecto_sap, imp, op_act, logs
                    )
                    if so_id is None:
                        logs.append(f"❌ Coincidencia exacta no hallada => fallback (ID={imp_id}).")
                        (sap_id, prod_order, op, op_act) = fallback_fuera_sistema(db, imp, logs)
                    else:
                        sap_id = so_id
                        prod_order = so_order

        # Si el fallback devolvió None => no insertamos la imputación
        if sap_id is None:
            logs.append(
                f"⚠️ Imputación ID={imp_id} DESCARTADA => sin SapOrder y sin 'FUERA_SISTEMA'."
            )
            continue

        new_row = TablaCentral(
            imputacion_id=imp_id,
            sap_order_id=sap_id,
            Employee_Number=imp.CodEmpleado,
            Date=imp.FechaImp,
            HourType="Production Direct Hour",
            ProductionOrder=prod_order,
            Operation=op,
            OperationActivity=op_act,
            Hours=imp.Horas,
            Cargado_SAP=False
        )
        db.add(new_row)
        db.commit()
        logs.append(f"✅ Imputación {imp_id} insertada en TablaCentral => SapOrder={sap_id}.")
