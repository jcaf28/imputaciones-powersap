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
        return 0

    logs.append(f"Encontradas {len(imps_pendientes)} imputaciones pendientes.")
    extraciclos_all = db.query(Extraciclos).all()

    # Contadores de resultado
    matched_count = 0
    discarded_no_operation = 0
    discarded_no_project = 0
    discarded_no_sap_match = 0
    discarded_not_found = 0

    for i_dict in imps_pendientes:
        imp_id = i_dict["id"]
        imp = db.query(Imputaciones).filter(Imputaciones.ID == imp_id).first()
        if not imp:
            logs.append(f"❌ Imputación ID={imp_id} no se encontró en BD.")
            discarded_not_found += 1
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
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: sin operation/operationActivity (Tarea={imp.Tarea}, TareaAsoc={imp.TareaAsoc}).")
                discarded_no_operation += 1
                continue

            # -----------------------------------------------------------
            # 3) Traducir proyecto BAAN → SAP
            # -----------------------------------------------------------
            proyecto_sap = obtener_proyecto_sap(imp.Proyecto, db)
            if not proyecto_sap:
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: proyecto SAP no encontrado para '{imp.Proyecto}'.")
                discarded_no_project += 1
                continue

            # -----------------------------------------------------------
            # 4) Match exacto (proyecto + vértice + coche + OA)
            # -----------------------------------------------------------
            so_id, so_order = obtener_sap_order_id_y_production_order_via_db(
                db, proyecto_sap, imp, op_act, logs
            )
            if so_id is None:
                logs.append(f"⚠️ Imputación ID={imp_id} DESCARTADA: sin coincidencia exacta en SAP (Proy={proyecto_sap}, Vert={imp.TipoCoche}, Coche={imp.NumCoche}, OA={op_act}).")
                discarded_no_sap_match += 1
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

        matched_count += 1
        logs.append(
            f"✅ Imputación ID={imp_id} insertada => SapOrder={sap_id}."
        )

    # Resumen final
    total = len(imps_pendientes)
    total_discarded = discarded_not_found + discarded_no_operation + discarded_no_project + discarded_no_sap_match
    logs.append(f"📊 RESUMEN: {matched_count}/{total} asignadas, {total_discarded} descartadas.")
    if discarded_no_operation > 0:
        logs.append(f"   - Sin operation/operationActivity: {discarded_no_operation}")
    if discarded_no_project > 0:
        logs.append(f"   - Sin proyecto SAP: {discarded_no_project}")
    if discarded_no_sap_match > 0:
        logs.append(f"   - Sin coincidencia exacta en SAP: {discarded_no_sap_match}")
    if discarded_not_found > 0:
        logs.append(f"   - No encontradas en BD: {discarded_not_found}")
    if matched_count == 0:
        logs.append("⚠️ ATENCIÓN: Ninguna imputación pudo ser asignada. No se generará ZIP.")

    return matched_count
