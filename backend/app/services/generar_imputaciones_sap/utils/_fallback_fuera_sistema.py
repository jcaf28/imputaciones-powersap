# PATH: backend/app/services/generar_imputaciones_sap/utils/_fallback_fuera_sistema.py

from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import SapOrders, Imputaciones, Areas, Extraciclos  # ← añadido Extraciclos
from string import ascii_uppercase

def get_vertex_rank(vertice: str) -> int:
    if len(vertice) != 1:
        return 9999
    try:
        return ascii_uppercase.index(vertice.upper())
    except ValueError:
        return 9999

def get_vertex_priority_list(vertice_actual: str) -> List[str]:
    r = get_vertex_rank(vertice_actual)
    all_letters = list(ascii_uppercase)
    inf = [v for v in all_letters if get_vertex_rank(v) < r]
    sup = [v for v in all_letters if get_vertex_rank(v) > r]
    inf_desc = sorted(inf, key=lambda x: get_vertex_rank(x), reverse=True)
    sup_asc = sorted(sup, key=lambda x: get_vertex_rank(x))
    return [vertice_actual] + inf_desc + sup_asc

def fallback_fuera_sistema(
    db: Session,
    imp: Imputaciones,
    logs: List[str]
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    """
    Fallback revisado para casos con Extraciclos:

      • Si imp.TareaAsoc NO es nulo:
          1) Obtiene el OASAP en Extraciclos (area_tarea = imp.AreaTarea).
          2) Si existe → filtra SapOrders activas por ese OperationActivity
             y prioriza Vértice y CarNumber.
          3) Si no existe OASAP → salta directamente a la lógica 'C0'.
      • Si imp.TareaAsoc ES nulo → usa la lógica original basada en imp.Tarea.

      Después se mantienen, por este orden:
        – lógica 'C0'  (Areas.OpMinC)
        – orden genérica 'FUERA_SISTEMA'
    """
    # 0) Verificar que exista ProyectoSap
    proyecto_sap = getattr(imp.project_dict, "ProyectoSap", None)
    if not proyecto_sap:
        logs.append("No hay ProyectoSap → se buscará 'FUERA_SISTEMA'.")
        return _fuera_sistema_only(db, logs)

    try:
        current_car = int(imp.NumCoche) if imp.NumCoche else None
    except ValueError:
        current_car = None

    # 1) Órdenes activas del proyecto
    orders = db.query(SapOrders).filter(
        SapOrders.Project == proyecto_sap,
        SapOrders.ActiveOrder == True
    ).all()
    if not orders:
        logs.append(f"No hay órdenes activas para {proyecto_sap} → 'FUERA_SISTEMA'.")
        return _fuera_sistema_only(db, logs)

    # 2) Ámbito de búsqueda principal
    same_orders: List[SapOrders] = []
    if imp.TareaAsoc:                    # ← CASO EXTRACICLO
        extra = db.query(Extraciclos).filter(
            Extraciclos.AreaTarea == imp.AreaTarea
        ).first()
        if extra and extra.OASAP:
            target_oa = extra.OASAP
            same_orders = [o for o in orders if o.OperationActivity == target_oa]
            descr = f"OA='{target_oa}'"
        else:
            descr = "extraciclo sin OASAP"
    else:                                # ← RESTO DE ÓRDENES
        if imp.Tarea:
            same_orders = [o for o in orders if o.Operation == imp.Tarea]
            descr = f"OP='{imp.Tarea}'"
        else:
            descr = "sin Tarea"

    if same_orders:
        vert_list = get_vertex_priority_list(imp.TipoCoche or "")
        candidates = [
            _pick_by_car_number([o for o in same_orders if o.Vertice == v], current_car)
            for v in vert_list
        ]
        picked = next((c for c in candidates if c), None)
        if picked:
            logs.append(f"Fallback → SapOrder ID={picked.ID} ({descr}, v={picked.Vertice})")
            return (picked.ID, picked.Order, picked.Operation, picked.OperationActivity)
        logs.append(f"No se halló orden con {descr} tras priorizar vértice/coche.")
    else:
        logs.append(f"No se encontraron órdenes con {descr}.")

    # 3) Lógica 'C0' (Areas.OpMinC)
    op_min_c = getattr(
        db.query(Areas).filter(Areas.CentroTrabajo == imp.area_id).first(),
        "OpMinC",
        None,
    )
    if op_min_c:
        same_vertex = [
            o for o in orders
            if o.OperationActivity == op_min_c and o.Vertice == imp.TipoCoche
        ]
        if same_vertex:
            same_vertex.sort(key=lambda x: x.CarNumber or 999999)
            chosen = same_vertex[0]
            logs.append(f"Fallback → 'C0 logic' con orden ID={chosen.ID}")
            return (chosen.ID, chosen.Order, chosen.Operation, chosen.OperationActivity)

        any_vertex = [o for o in orders if o.OperationActivity == op_min_c]
        if any_vertex:
            any_vertex.sort(key=lambda x: x.CarNumber or 999999)
            chosen2 = any_vertex[0]
            logs.append(f"Fallback → 'C0 logic' sin vértice con orden ID={chosen2.ID}")
            return (chosen2.ID, chosen2.Order, chosen2.Operation, chosen2.OperationActivity)

    # 4) Orden genérica 'FUERA_SISTEMA'
    logs.append("Sin coincidencias → se asignará 'FUERA_SISTEMA'.")
    return _fuera_sistema_only(db, logs)

def _fuera_sistema_only(
    db: Session,
    logs: List[str]
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    so = db.query(SapOrders).filter(
        SapOrders.ActiveOrder == True,
        SapOrders.Operation == "FUERA_SISTEMA"
    ).order_by(desc(SapOrders.TimestampInput)).first()
    if so:
        logs.append(f"Asignada la orden genérica 'FUERA_SISTEMA' (ID={so.ID}).")
        return (so.ID, so.Order, so.Operation, so.OperationActivity)

    logs.append("⚠️ No se encontró 'FUERA_SISTEMA'. Se descarta la imputación.")
    return (None, None, None, None)

def _pick_by_car_number(orders: List[SapOrders], car_number: Optional[int]) -> Optional[SapOrders]:
    if not orders:
        return None
    if not car_number:
        sorted_ords = sorted(orders, key=lambda x: x.CarNumber if x.CarNumber else 999999)
        return sorted_ords[0]
    below = [o for o in orders if o.CarNumber and o.CarNumber < car_number]
    below.sort(key=lambda x: x.CarNumber if x.CarNumber else 999999, reverse=True)
    if below:
        return below[0]
    above = [o for o in orders if o.CarNumber and o.CarNumber > car_number]
    above.sort(key=lambda x: x.CarNumber if x.CarNumber else 999999)
    if above:
        return above[0]
    return None
