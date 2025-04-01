# PATH: manual-imputaciones-ip/etl/_utils.py

import pandas as pd

def verificar_mes_unico(df, columna_fechas="Intervalo de fechas"):
    """
    Verifica que todos los registros en la columna de intervalo de fechas 
    pertenecen al mismo mes. Asume que los valores están en formato "YYYY-MM-DD to YYYY-MM-DD".
    """
    # Extraer los meses de la columna de fechas
    meses = df[columna_fechas].apply(lambda x: pd.to_datetime(x.split(" to ")[0]).month)
    
    # Comprobar si todos los meses son iguales
    if meses.nunique() > 1:
        raise ValueError("El archivo de fichajes contiene intervalos de fechas que no pertenecen al mismo mes.")
    
    return True

def extraer_centro_por_chapa(fichajes_sap, chapa_col='Número de empleado', centro_col='Centro'):
    """
    Devuelve un DataFrame con las columnas 'chapa' y 'centro' para cada empleado 
    según los registros en fichajes_sap.
    """
    return fichajes_sap[[chapa_col, centro_col]].rename(columns={chapa_col: 'chapa', centro_col: 'centro'})

def extraer_fecha_imputacion(fichajes_sap, intervalo_fechas_col='Intervalo de fechas'):
    """
    Extrae la última fecha del mes natural en el cual está inserto el intervalo de fechas
    y devuelve un DataFrame con 'chapa' y 'fecha_imput'.
    
    Parámetros:
    - fichajes_sap: DataFrame que contiene los datos de fichajes.
    - intervalo_fechas_col: Nombre de la columna que contiene el intervalo de fechas.
    
    Retorna:
    - DataFrame con las columnas 'chapa' y 'fecha_imput' que corresponde a la última
      fecha del mes natural de la fecha extraída.
    """
    # Copiamos las columnas relevantes
    fecha_imput = fichajes_sap[[intervalo_fechas_col, 'Número de empleado']].copy()
    
    # Extraemos la última fecha del intervalo
    fecha_imput['fecha_imput'] = fecha_imput[intervalo_fechas_col].apply(
        lambda x: x.split(' to ')[-1].strip()
    )
    
    # Convertimos la fecha extraída a tipo datetime
    fecha_imput['fecha_imput'] = pd.to_datetime(fecha_imput['fecha_imput'], format='%Y-%m-%d')
    
    # Calculamos la última fecha del mes natural correspondiente
    fecha_imput['fecha_imput'] = fecha_imput['fecha_imput'] + pd.offsets.MonthEnd(0)
    
    # Renombramos la columna 'Número de empleado' a 'chapa' y seleccionamos las columnas finales
    return fecha_imput.rename(columns={'Número de empleado': 'chapa'})[['chapa', 'fecha_imput']]

def reordenar_y_formatear_columnas(df):
    """
    Reordena y formatea las columnas de `df` según el formato especificado:
    - Reordena las columnas en el orden específico.
    - Convierte 'fecha_imput' al formato 'dd/mm/YYYY'.
    - Añade dos columnas vacías llamadas 'Vacía1' y 'Vacía2'.

    Parámetros:
        df (pd.DataFrame): El DataFrame de entrada.

    Retorna:
        pd.DataFrame: El DataFrame modificado con el orden y formato de columnas deseado.
    """
    # Convertir 'fecha_imput' a formato 'dd/mm/YYYY'
    df['fecha_imput'] = pd.to_datetime(df['fecha_imput']).dt.strftime('%d/%m/%Y')

    # Añadir columnas vacías 'Vacía1' y 'Vacía2'
    df['Vacía1'] = ''
    df['Vacía2'] = ''

    # Seleccionar y reordenar las columnas
    columnas_finales = [
        'centro',
        'fecha_imput',
        'chapa',
        'Horas',
        'Cost',
        'Cost_2',
        'WBS',
        'Vacía1',
        'Vacía2',
        'PSA'
    ]
    df = df[columnas_finales]

    return df

def dividir_horas(df, max_horas=90):
    """
    Divide las imputaciones que excedan un máximo de horas en múltiples filas de máximo `max_horas`.
    
    Parameters:
    - df (pd.DataFrame): DataFrame que contiene las imputaciones con columnas 'chapa', 'OBRA_1' y 'Horas'.
    - max_horas (int): Límite máximo de horas por fila.
    
    Returns:
    - pd.DataFrame: DataFrame con filas divididas en grupos de máximo `max_horas`.
    """
    rows = []
    for _, row in df.iterrows():
        horas = row['Horas']
        while horas > max_horas:
            row_copy = row.copy()
            row_copy['Horas'] = max_horas
            rows.append(row_copy)
            horas -= max_horas
        row['Horas'] = round(horas, 2)  # Redondeo del valor final antes de añadir
        rows.append(row)
    return pd.DataFrame(rows)