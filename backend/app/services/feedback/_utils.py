# PATH: backend/app/services/feedback/_utils.py

import pandas as pd

def change_dtypes(df):
    df['CodEmpleado'] = df['CodEmpleado'].astype(str).str.replace('.0', '', regex=False)
    df['Timpu'] = df['Timpu'].astype(str).str.replace('.0', '', regex=False)
    df['Horas'] = df['Horas'].astype(float).round(2)
    df['Proyecto'] = df['Proyecto'].astype(str).str.replace('.0', '', regex=False)
    df['TipoCoche'] = df['TipoCoche'].astype(str)
    df['NumCoche'] = df['NumCoche'].astype(str).str.replace('.0', '', regex=False)
    df['CentroTrabajo'] = df['CentroTrabajo'].astype(str).str.replace('.0', '', regex=False)
    df['Tarea'] = df['Tarea'].astype(str).str.replace('.0', '', regex=False)
    df['TareaAsoc'] = df['TareaAsoc'].astype(str).str.replace('.0', '', regex=False)

    return(df)

def _filtrar_fechas_parseables(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={'Fecha': 'FechaImp'}) if 'Fecha' in df.columns else df

    def parsear_fecha(fecha):
        try:
            return pd.to_datetime(fecha, format="%d/%m/%Y").date()
        except:
            return None

    df["FechaImp"] = df["FechaImp"].apply(parsear_fecha)
    return df[df["FechaImp"].notna()]

def is_null(value) -> bool:
    """True si el valor es None, NaN o string 'nan'."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() == "nan":
        return True
    if pd.isna(value):
        return True
    return False

def intercambiar_tareas(df):
    # Intercambiar valores de 'Tarea' y 'TareaAsoc' solo si 'TareaAsoc' no está en blanco ni es nulo
    for index, row in df.iterrows():
        if not is_null(row['TareaAsoc']) and row['TareaAsoc'] != '':
            # Asegúrate de que 'TareaAsoc' sea una cadena antes de llamar a replace
            tarea_asoc_str = str(row['TareaAsoc'])
            tarea_asoc_str = tarea_asoc_str.replace('.0', '')
            row['TareaAsoc'] = tarea_asoc_str
            # Intercambio de valores
            df.at[index, 'Tarea'], df.at[index, 'TareaAsoc'] = row['TareaAsoc'], row['Tarea']

    return df