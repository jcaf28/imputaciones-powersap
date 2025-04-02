# PATH: backend/app/services/imputaciones_ip/loader.py

import pandas as pd
from ._constants_imputaciones import COLUMNAS_MINIMAS
from ._utils import verificar_mes_unico

def cargar_y_limpiar_datos(*paths):
    dataframes = []
    tabla_nombres = ["wbs_por_clave", "listado_usuarios", "descarga_imputaciones", "fichajes_sap"]
    
    for nombre_tabla, path in zip(tabla_nombres, paths):
        # Configurar la lectura del archivo según la tabla
        if nombre_tabla == "descarga_imputaciones":
            df = pd.read_excel(path, dtype={"OBRA_1": str})
        else:
            df = pd.read_excel(path)
        
        # Eliminar espacios en columnas que sean de tipo string, ignorando nulos
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

            #el dtype de esa columna se queda como string, no como object
            df[col] = df[col].astype(str)
        
        # Verificar que las columnas mínimas estén presentes en el archivo
        columnas_faltantes = [col for col in COLUMNAS_MINIMAS[nombre_tabla] if col not in df.columns]
        if columnas_faltantes:
            raise ValueError(f"El archivo '{nombre_tabla}' no tiene las siguientes columnas mínimas necesarias: {', '.join(columnas_faltantes)}")
        
        # Verificar que todos los registros de 'Intervalo de fechas' pertenezcan al mismo mes para fichajes_sap
        if nombre_tabla == "fichajes_sap":
            verificar_mes_unico(df)

        dataframes.append(df)
    
    return dataframes
