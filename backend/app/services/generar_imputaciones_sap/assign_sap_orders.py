from typing import List
from sqlalchemy.orm import Session
from app.models.models import (
    Imputaciones, TablaCentral, Extraciclos
)
from app.services.generar_imputaciones_sap.pending_imputaciones import get_imputaciones_pendientes
from .utils._assign_sap_orders import (
    obtener_operation_via_db,
    obtener_proyecto_sap,
    obtener_sap_order_id_y_production_order_via_db,
    obtener_sap_order_gg
)

def run_assign_sap_orders_inmemory(db: Session, logs: List[str]):
    """
    1) Limpia Tabla_Central de filas previas con Cargado_SAP=False.
    2) Obtiene las imputaciones pendientes.
    3) Para cada imputación:
        - Busca coincidencia GG.
        - Si no hay GG: resuelve operation/operationActivity.
        - Traduce proyecto BAAN → SAP.
        - Busca match exacto (proyecto + vértice + coche + OA).
        - Si no hay match en cualquier paso → DESCARTA la imputación.
    """

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

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp:
            logs.append(f"❌ Imputación ID={imp_id} no se encontró en BD.")
            continue

        logs.append(f"🔧 Procesando imputación ID={imp_id}...")

        # -----------------------------------------------------------
        # 1) Intento por TipoIndirecto + TipoMotivo => GG
        # -----------------------------------------------------------
        so_indirecto = obtener_sap_order_gg(imp, db, logs)
        if so_indirecto:
            sap_id = so_indirecto.ID
            prod_order = so_indirecto.Order
            op = so_indirecto.Operation
            op_act = so_indirecto.OperationActivity
        else:
            # -----------------------------------------------------------
            # 2) Obtener operation, operationActivity
            # -----------------------------------------------------------
            op, op_act = obtener_operation_via_db(imp, db, extraciclos_all, logs)

            if op is None or op_act is None:
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: sin operation/operationActivity.")
                continue

            # -----------------------------------------------------------
            # 3) Traducir proyecto BAAN → SAP
            # -----------------------------------------------------------
            proyecto_sap = obtener_proyecto_sap(imp.Proyecto, db)
            if not proyecto_sap:
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: proyecto SAP no encontrado para '{imp.Proyecto}'.")
                continue

            # -----------------------------------------------------------
            # 4) Match exacto (proyecto + vértice + coche + OA)
            # -----------------------------------------------------------
            so_id, so_order = obtener_sap_order_id_y_production_order_via_db(
                db, proyecto_sap, imp, op_act, logs
            )
            if so_id is None:
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: sin coincidencia exacta en SAP.")
                continue

            sap_id = so_id
            prod_order = so_order

        # -----------------------------------------------------------
        # 5) Insertar en Tabla_Central
        # -----------------------------------------------------------
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
            Cargado_SAP=False,
        )
        db.add(new_row)
        db.commit()

        logs.append(
            f"✅ Imputación ID={imp_id} insertada => SapOrder={sap_id}."
        )
