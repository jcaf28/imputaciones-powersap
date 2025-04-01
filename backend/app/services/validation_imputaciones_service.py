# PATH: backend/app/services/validation_imputaciones_service.py

import pandas as pd
from .imputaciones_ip._constants_imputaciones import COLUMNAS_MINIMAS

def validate_imputaciones_file(filepath: str, file_type: str) -> None:
    """
    Valida que el archivo Excel contenga las columnas mínimas requeridas 
    para `file_type`. Lanza excepción si algo falla.

    :param filepath: ruta al archivo subido en /tmp
    :param file_type: uno de ("descarga_imputaciones", "listado_usuarios",
                            "wbs_por_clave", "fichajes_sap")
    :raises ValueError: si faltan columnas mínimas
    """
    # Leer el Excel
    if file_type == "descarga_imputaciones":
        df = pd.read_excel(filepath, dtype={"OBRA_1": str})
    else:
        df = pd.read_excel(filepath)

    # Eliminar espacios en columnas string
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        df[col] = df[col].astype(str)

    # Verificar columnas mínimas
    required_cols = COLUMNAS_MINIMAS[file_type]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas mínimas en {file_type}: {', '.join(missing)}")

    # TODO: en un futuro, chequear tipos, rangos, etc.

    # Devolver nada si OK
    return
