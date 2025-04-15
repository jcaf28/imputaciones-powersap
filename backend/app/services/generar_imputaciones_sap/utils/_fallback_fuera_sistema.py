# PATH: backend/app/services/generar_imputaciones_sap/utils/_fallback_fuera_sistema.py

from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import SapOrders, Imputaciones, Areas
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
    Lógica de fallback para cada imputación:
      1) Busca primero SapOrders activas para el mismo proyecto, Operation == imp.Tarea,
         prioriza CarNumber y Vértice.
      2) Si no encuentra => aplica 'C0 logic' (Areas.OpMinC).
      3) Si tampoco => busca SapOrder con Operation='FUERA_SISTEMA'.
      4) Si no existe => descarta la imputación (retornamos None para todos).
    """
    project_dict = imp.project_dict
    if not project_dict or not project_dict.ProyectoSap:
        logs.append("No hay ProyectoSap => se buscará 'FUERA_SISTEMA'.")
        return _fuera_sistema_only(db, logs)

    proyecto_sap = project_dict.ProyectoSap
    try:
        current_car_number = int(imp.NumCoche) if imp.NumCoche else None
    except ValueError:
        current_car_number = None

    # 1) Buscar órdenes activas del proyecto
    orders = db.query(SapOrders).filter(
        SapOrders.Project == proyecto_sap,
        SapOrders.ActiveOrder == True
    ).all()
    if not orders:
        logs.append(f"No hay órdenes SAP activas para {proyecto_sap} => 'FUERA_SISTEMA'.")
        return _fuera_sistema_only(db, logs)

    # 2) Filtrar Operation == imp.Tarea
    if not imp.Tarea:
        logs.append("La imputación no tiene Tarea => usar 'FUERA_SISTEMA'.")
        return _fuera_sistema_only(db, logs)

    same_op_orders = [o for o in orders if o.Operation == imp.Tarea]
    if same_op_orders:
        vert = imp.TipoCoche if imp.TipoCoche else ""
        priority_list = get_vertex_priority_list(vert)
        for v in priority_list:
            cand = [o for o in same_op_orders if o.Vertice == v]
            picked = _pick_by_car_number(cand, current_car_number) if cand else None
            if picked:
                logs.append(
                    f"Fallback => asignado SapOrder ID={picked.ID}, op={picked.Operation}, v={picked.Vertice}"
                )
                return (picked.ID, picked.Order, picked.Operation, picked.OperationActivity)

    # 3) "C0 logic" => busca Areas.OpMinC
    area = db.query(Areas).filter(Areas.CentroTrabajo == imp.area_id).first()
    op_min_c = area.OpMinC if area else None
    if op_min_c:
        same_v = [o for o in orders if o.OperationActivity == op_min_c and o.Vertice == imp.TipoCoche]
        if same_v:
            same_v.sort(key=lambda x: x.CarNumber if x.CarNumber else 999999)
            chosen = same_v[0]
            logs.append(f"Fallback => 'C0 logic' con orden ID={chosen.ID}")
            return (chosen.ID, chosen.Order, chosen.Operation, chosen.OperationActivity)

        no_vertex = [o for o in orders if o.OperationActivity == op_min_c]
        if no_vertex:
            no_vertex.sort(key=lambda x: x.CarNumber if x.CarNumber else 999999)
            chosen2 = no_vertex[0]
            logs.append(f"Fallback => 'C0 logic' sin vértice con orden ID={chosen2.ID}")
            return (chosen2.ID, chosen2.Order, chosen2.Operation, chosen2.OperationActivity)

    # 4) Nada => 'FUERA_SISTEMA'
    logs.append("No se encontró coincidencia => buscar 'FUERA_SISTEMA'.")
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
