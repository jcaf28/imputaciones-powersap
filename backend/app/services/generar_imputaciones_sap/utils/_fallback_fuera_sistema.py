# backend/app/services/generar_imputaciones_sap/utils/_fallback_fuera_sistema.py
"""
Fallback ‘FUERA SISTEMA’ con restricción de Área
(≤ 3 niveles de indentación).
"""

from __future__ import annotations
from string import ascii_uppercase
from typing import List, Tuple, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.models import SapOrders, Imputaciones, Areas, Extraciclos


# ───────────────────────────── utilidades simples ─────────────────────────────
def _vertex_rank(v: str) -> int:
    return ascii_uppercase.index(v.upper()) if v and v.upper() in ascii_uppercase else 9999


def _vertex_priority(cur: str) -> List[str]:
    letters = list(ascii_uppercase)
    below = [l for l in letters if _vertex_rank(l) < _vertex_rank(cur)]
    above = [l for l in letters if _vertex_rank(l) > _vertex_rank(cur)]
    return [cur] + sorted(below, reverse=True) + sorted(above)


def _pick_by_car(orders: List[SapOrders], car: Optional[int]) -> Optional[SapOrders]:
    if not orders:
        return None
    if car is None:
        return min(orders, key=lambda o: o.CarNumber or 999_999)
    below = [o for o in orders if o.CarNumber and o.CarNumber < car]
    if below:
        return max(below, key=lambda o: o.CarNumber)
    above = [o for o in orders if o.CarNumber and o.CarNumber > car]
    if above:
        return min(above, key=lambda o: o.CarNumber)
    return None


# ────────────────── nuevas utilidades de filtrado por Área ────────────────────
def _area_match(imp_area: str | None, order_area: str | None, proyecto: str | None = None, centro_trabajo: str | None = None) -> bool:
    if not imp_area or not order_area:
        return False
    a, b = imp_area.strip().lower(), order_area.strip().lower()
    if a == b:
        return True
    
    # Excepción para proyecto '1103' y CentroTrabajo '162': 
    # la caja de boston es de acero, no de aluminio, por lo que ea, eb y ba son intercambiables
    if proyecto == '1103' and centro_trabajo == '162':
        areas_intercambiables = {"ea", "eb", "ba"}
        return a in areas_intercambiables and b in areas_intercambiables
    
    # Lógica normal: solo ea y eb son intercambiables
    eb_ea = {"ea", "eb"}
    return a in eb_ea and b in eb_ea


def _filter_orders_by_area(
    orders: List[SapOrders], imp_area: str | None, proyecto: str | None = None, centro_trabajo: str | None = None
) -> List[SapOrders]:
    if not imp_area:
        return orders
    return [o for o in orders if _area_match(imp_area, o.Area, proyecto, centro_trabajo)]


# ────────────────────────────── bloques de búsqueda ───────────────────────────
def _orders_project(db: Session, project: str) -> List[SapOrders]:
    return (
        db.query(SapOrders)
        .filter(SapOrders.Project == project, SapOrders.ActiveOrder.is_(True))
        .all()
    )


def _orders_extraciclo(
    db: Session, imp: Imputaciones, orders: List[SapOrders], logs: List[str]
) -> Tuple[List[SapOrders], str]:
    extra = db.query(Extraciclos).filter(Extraciclos.AreaTarea == imp.AreaTarea).first()
    oa = getattr(extra, "OASAP", None)
    if not oa:
        return [], "extraciclo sin OASAP"

    same = [o for o in orders if o.OperationActivity == oa]
    if same:
        return same, f"OA exacta '{oa}'"

    tipo = oa[-2:]
    tipo_orders = [o for o in orders if o.OperationActivity and o.OperationActivity.endswith(tipo)]
    if not tipo_orders:
        return [], f"sin OA tipo '{tipo}'"

    primer_oa = sorted({o.OperationActivity for o in tipo_orders})[0]
    same = [o for o in tipo_orders if o.OperationActivity == primer_oa]
    return same, f"OA tipo '{tipo}' → '{primer_oa}'"


def _orders_tarea(imp: Imputaciones, orders: List[SapOrders]) -> Tuple[List[SapOrders], str]:
    if not imp.Tarea:
        return [], "sin Tarea"
    same = [o for o in orders if o.Operation == imp.Tarea]
    return same, f"Operation '{imp.Tarea}'"


def _c0_logic(
    db: Session, orders: List[SapOrders], imp: Imputaciones, logs: List[str]
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    op_c0 = getattr(
        db.query(Areas).filter(Areas.CentroTrabajo == imp.area_id).first(), "OpMinC", None
    )
    if not op_c0:
        return _fuera_sistema(db, logs)

    same_vertex = [
        o for o in orders if o.OperationActivity == op_c0 and o.Vertice == imp.TipoCoche
    ]
    if same_vertex:
        chosen = min(same_vertex, key=lambda o: o.CarNumber or 999_999)
        logs.append(f"C0 → ID={chosen.ID}")
        return chosen.ID, chosen.Order, chosen.Operation, chosen.OperationActivity

    any_vertex = [o for o in orders if o.OperationActivity == op_c0]
    if any_vertex:
        chosen = min(any_vertex, key=lambda o: o.CarNumber or 999_999)
        logs.append(f"C0 sin vértice → ID={chosen.ID}")
        return chosen.ID, chosen.Order, chosen.Operation, chosen.OperationActivity

    return _fuera_sistema(db, logs)


def _fuera_sistema(
    db: Session, logs: List[str]
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    so = (
        db.query(SapOrders)
        .filter(SapOrders.ActiveOrder.is_(True), SapOrders.Operation == "FUERA_SISTEMA")
        .order_by(desc(SapOrders.TimestampInput))
        .first()
    )
    if so:
        logs.append(f"Asignada 'FUERA_SISTEMA' (ID={so.ID})")
        return so.ID, so.Order, so.Operation, so.OperationActivity

    logs.append("⚠️ No existe 'FUERA_SISTEMA'")
    return None, None, None, None


# ────────────────────────────── flujo principal ───────────────────────────────
def fallback_fuera_sistema(
    db: Session, imp: Imputaciones, logs: List[str]
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    proyecto = getattr(imp.project_dict, "ProyectoSap", None)
    if not proyecto:
        return _fuera_sistema(db, logs)

    orders = _orders_project(db, proyecto)

    # ─── filtrado por Área ───
    imp_area = getattr(getattr(imp, "area", None), "Area", None)
    orders = _filter_orders_by_area(orders, imp_area, proyecto, imp.CentroTrabajo)
    if not orders:
        logs.append(
            f"No hay órdenes activas para proyecto '{proyecto}' tras filtrar por área."
        )
        return _fuera_sistema(db, logs)

    try:
        car = int(imp.NumCoche) if imp.NumCoche else None
    except ValueError:
        car = None

    if imp.TareaAsoc:
        same, descr = _orders_extraciclo(db, imp, orders, logs)
    else:
        same, descr = _orders_tarea(imp, orders)

    if same:
        for v in _vertex_priority(imp.TipoCoche or ""):
            pick = _pick_by_car([o for o in same if o.Vertice == v], car)
            if pick:
                logs.append(f"Fallback → {descr}, v={v}, ID={pick.ID}")
                return pick.ID, pick.Order, pick.Operation, pick.OperationActivity
        logs.append(f"Sin vértice/coche apropiados para {descr}.")
    else:
        logs.append(f"No se encontraron órdenes con {descr}.")

    return _c0_logic(db, orders, imp, logs)
