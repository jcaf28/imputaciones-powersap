# PATH: backend/app/services/feedback/_utils.py

import pandas as pd

def change_dtypes(df):
    # Con dtype=str en read_excel, los campos ya son str.
    # Solo convertimos Horas a float.
    df['Horas'] = pd.to_numeric(df['Horas'], errors='coerce').round(2)
    return df

def _filtrar_fechas_parseables(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={'Fecha': 'FechaImp'}) if 'Fecha' in df.columns else df

    def parsear_fecha(fecha):
        try:
            return pd.to_datetime(fecha, dayfirst=True).date()
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
            df.at[index, 'Tarea'], df.at[index, 'TareaAsoc'] = row['TareaAsoc'], row['Tarea']

    return df