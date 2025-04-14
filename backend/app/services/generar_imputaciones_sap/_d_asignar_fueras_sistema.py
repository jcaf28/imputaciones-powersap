from string import ascii_uppercase

# Funciones auxiliares "get" para buscar_orden_sap_alternativa

def get_vertex_rank(vertice: str) -> int:
    """
    Retorna la posición del vértice dentro de ascii_uppercase.
    Si no existe o es más de un carácter, retorna 9999.
    """
    if len(vertice) != 1:
        return 9999
    try:
        return ascii_uppercase.index(vertice.upper())
    except ValueError:
        return 9999

def get_vertex_priority_list(vertice_actual: str) -> list:
    """
    Genera una lista con:
      - el vértice actual
      - vértices 'inferiores' (menor rank) en orden descendente
      - vértices 'superiores' (mayor rank) en orden ascendente
    """
    r = get_vertex_rank(vertice_actual)
    all_letters = list(ascii_uppercase)

    inferiores = [v for v in all_letters if get_vertex_rank(v) < r]
    superiores = [v for v in all_letters if get_vertex_rank(v) > r]

    inf_desc = sorted(inferiores, key=lambda x: get_vertex_rank(x), reverse=True)
    sup_asc = sorted(superiores, key=lambda x: get_vertex_rank(x))

    return [vertice_actual] + inf_desc + sup_asc