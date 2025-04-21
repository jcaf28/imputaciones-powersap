# PATH: backend/app/services/feedback/_utils.py

import pandas as pd


def change_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los tipos de columna y elimina los sufijos '.0' que aparecen
    al leer números desde Excel.
    """
    df["CodEmpleado"]   = df["CodEmpleado"].astype(str).str.replace(".0", "", regex=False)
    df["Timpu"]         = df["Timpu"].astype(str).str.replace(".0", "", regex=False)
    df["Horas"]         = df["Horas"].astype(float).round(2)
    df["Proyecto"]      = df["Proyecto"].astype(str).str.replace(".0", "", regex=False)
    df["TipoCoche"]     = df["TipoCoche"].astype(str)
    df["NumCoche"]      = df["NumCoche"].astype(str).str.replace(".0", "", regex=False)
    df["CentroTrabajo"] = df["CentroTrabajo"].astype(str).str.replace(".0", "", regex=False)
    df["Tarea"]         = df["Tarea"].astype(str).str.replace(".0", "", regex=False)
    df["TareaAsoc"]     = df["TareaAsoc"].astype(str).str.replace(".0", "", regex=False)
    return df


def intercambiar_tareas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Si 'TareaAsoc' está informada, limpia su '.0' y la intercambia con 'Tarea'.
    """
    for idx, row in df.iterrows():
        if pd.notna(row["TareaAsoc"]) and str(row["TareaAsoc"]).strip():
            tarea_asoc = str(row["TareaAsoc"]).replace(".0", "")
            df.at[idx, "TareaAsoc"] = tarea_asoc
            df.at[idx, "Tarea"], df.at[idx, "TareaAsoc"] = (
                df.at[idx, "TareaAsoc"],
                df.at[idx, "Tarea"],
            )
    return df
