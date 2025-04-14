from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, joinedload
import logging

from app.models.models import (
    Imputaciones,
    SapOrders,
    Areas,
    Extraciclos
)
from ._d_asignar_fueras_sistema import (
    get_vertex_rank,
    get_vertex_priority_list
)

def fallback_realista(
    imp: Imputaciones,
    db: Session,
    dict_extraciclos: Dict[str, str],
    logs: List[str],
    incluir_GG: bool = True
) -> Optional[int]:
    """
    Lógica fallback 'realista' para una sola Imputaciones:
    1) Ajuste Tarea/TareaAsoc con Extraciclos (si TareaAsoc).
    2) Si ProyectoSap='Gasto General' y incluir_GG=True => asignar_orden_sap_gg.
    3) Si no => buscar_sap_order_alternativa (C0, priorizar Tarea y CarNumber, etc.)
    4) Si no => fallback_fuera_sistema.

    Retorna sap_order_id o None si no encuentra.
    """
    logs.append(f"⏬ Fallback realista => ID={imp.ID}, Tarea={imp.Tarea}, TAsoc={imp.TareaAsoc}")

    # 1) Ajustar Tarea/TareaAsoc según Extraciclos
    if imp.TareaAsoc and imp.AreaTarea in dict_extraciclos:
        oasap = dict_extraciclos[imp.AreaTarea]  # p.ej. 'XY-123'
        logs.append(f"Extraciclos => OASAP={oasap}")
        partes = oasap.split('-')
        if len(partes) == 2:
            # Intercambiamos
            imp.TareaAsoc = partes[0]
            imp.Tarea = partes[1]
            logs.append(f"Tarea y TareaAsoc intercambiadas => Tarea={imp.Tarea}, TAsoc={imp.TareaAsoc}")

    # (Re)cargamos su project_dict, por si no lo tenía
    if not getattr(imp, 'project_dict', None):
        db.refresh(imp)  # Asegurar
    proyecto_sap = imp.project_dict.ProyectoSap if imp.project_dict else None
    logs.append(f"ProyectoSap={proyecto_sap}")

    # 2) Si es 'Gasto General' => asignar_orden_sap_gg
    if incluir_GG and proyecto_sap == "Gasto General":
        sap_id = asignar_orden_sap_gg(db, imp, logs)
        if sap_id:
            return sap_id
        logs.append("No se pudo asignar SapOrder GG => se probará la alternativa...")

    # 3) Buscar sap_order_alternativa => Tarea, CarNumber, priorizar vértices
    sap_id = buscar_sap_order_alternativa(db, imp, logs)
    if sap_id:
        return sap_id

    # 4) Nada => “FUERA_SISTEMA”
    from ._assign_sap_orders import fallback_fuera_sistema
    logs.append("No se encontró SapOrder alternativa => probamos 'FUERA_SISTEMA'.")
    final_id = fallback_fuera_sistema(db, logs)
    return final_id


def asignar_orden_sap_gg(db: Session, imp: Imputaciones, logs: List[str]) -> Optional[int]:
    """
    Lógica Gasto General: 
    - Se intenta deducir una SapOrder con .Project='Gasto General', etc.
    - O bien, se buscan 'imputaciones_relacionadas' y se asigna 
      en base a la mayor 'Horas' u otra heurística
    """
    logs.append(f"⏬ asignar_orden_sap_gg => ID={imp.ID}")
    # Podrías reusar la lógica de 'buscar_imputaciones_relacionadas' si la tienes
    # o simplemente filtrar SapOrders donde Project='Gasto General', etc.

    # 1) Filtrar sap_orders Project='Gasto General'
    so = (
        db.query(SapOrders)
        .filter(
            SapOrders.ActiveOrder == True,
            SapOrders.Project == "Gasto General",
            SapOrders.Vertice == imp.TipoCoche,
            SapOrders.CarNumber == imp.NumCoche
        )
        .order_by(desc(SapOrders.TimestampInput))
        .first()
    )
    if so:
        logs.append(f"Gasto General => sap_order_id={so.ID}")
        return so.ID

    logs.append("No se encontró SapOrder GG compatible.")
    return None


def buscar_sap_order_alternativa(db: Session, imp: Imputaciones, logs: List[str]) -> Optional[int]:
    """
    Modo 'chapucero' => priorizamos Tarea, CarNumber,
    luego ajustamos vértices superior/inferior, y si no => 'C0' => OpMinC
    """
    logs.append(f"⏬ buscar_sap_order_alternativa => ID={imp.ID}, Tarea={imp.Tarea}, TareaAsoc={imp.TareaAsoc}")

    # 1) Tomamos SapOrders del mismo ProyectoSap, si lo hay
    proyecto_sap = imp.project_dict.ProyectoSap if imp.project_dict else None
    if not proyecto_sap:
        logs.append("Imputación sin project_dict => None")
        return None

    # 2) Filtramos
    all_orders_for_project = (
        db.query(SapOrders)
        .filter(SapOrders.Project == proyecto_sap, SapOrders.ActiveOrder == True)
        .all()
    )
    if not all_orders_for_project:
        logs.append("No hay SapOrders activos para su proyecto => None")
        return None

    # 3) Filtramos las que tengan Operation == imp.Tarea
    tarea = imp.Tarea
    orders_same_task = [o for o in all_orders_for_project if o.Operation == tarea]
    # 4) Lógica de priorizar CarNumber inferior/superior, vértice “inferior/superior”
    if orders_same_task:
        current_car_number = None
        try:
            current_car_number = int(imp.NumCoche) if imp.NumCoche else None
        except ValueError:
            pass

        vert_priority_list = get_vertex_priority_list(imp.TipoCoche) if imp.TipoCoche else [imp.TipoCoche]
        for v in vert_priority_list:
            cand_orders = [o for o in orders_same_task if o.Vertice == v]
            found = _pick_by_car_number(cand_orders, current_car_number)
            if found:
                logs.append(f"Encontrada SapOrder => ID={found.ID}")
                return found.ID

    # 5) Si no encontraste nada con Operation == Tarea, fallback C0 => OpMinC
    order_c0_id = _fallback_c0_logic(imp, all_orders_for_project, db, logs)
    return order_c0_id


def _pick_by_car_number(orders: List[SapOrders], current_car_number: Optional[int]) -> Optional[SapOrders]:
    if not orders or current_car_number is None:
        return None
    below = [o for o in orders if o.CarNumber < current_car_number]
    below.sort(key=lambda x: x.CarNumber, reverse=True)
    if below:
        return below[0]
    above = [o for o in orders if o.CarNumber > current_car_number]
    above.sort(key=lambda x: x.CarNumber)
    if above:
        return above[0]
    return None


def _fallback_c0_logic(imp: Imputaciones, all_orders: List[SapOrders], db: Session, logs: List[str]) -> Optional[int]:
    """
    Lógica 'C0': 
    1) Miramos op_min_c
    2) Buscamos con OperationActivity == op_min_c
       - primero con su mismo vértice
       - si no, sin vértice
    """
    logs.append(f"⏬ fallback_c0 => ID={imp.ID}")
    area = db.query(Areas).filter(Areas.CentroTrabajo == imp.area_id).first()
    op_min_c = area.OpMinC if area else None
    if not op_min_c:
        logs.append("No op_min_c => None")
        return None

    same_vertex = [o for o in all_orders if o.OperationActivity == op_min_c and o.Vertice == imp.TipoCoche]
    same_vertex.sort(key=lambda x: x.CarNumber)
    if same_vertex:
        chosen = same_vertex[0]
        logs.append(f"C0 => same_vertex => {chosen.ID}")
        return chosen.ID

    no_vertex = [o for o in all_orders if o.OperationActivity == op_min_c]
    no_vertex.sort(key=lambda x: x.CarNumber)
    if no_vertex:
        chosen = no_vertex[0]
        logs.append(f"C0 => no_vertex => {chosen.ID}")
        return chosen.ID

    logs.append("C0 => no se encontró => None")
    return None
