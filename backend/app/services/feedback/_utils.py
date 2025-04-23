# PATH: backend/app/services/feedback/_utils.py

import pandas as pd

def intercambiar_tareas(df):
    # Intercambiar valores de 'Tarea' y 'TareaAsoc' solo si 'TareaAsoc' no está en blanco ni es nulo
    for index, row in df.iterrows():
        if pd.notna(row['TareaAsoc']) and row['TareaAsoc'] != '':
            # Asegúrate de que 'TareaAsoc' sea una cadena antes de llamar a replace
            tarea_asoc_str = str(row['TareaAsoc'])
            tarea_asoc_str = tarea_asoc_str.replace('.0', '')
            row['TareaAsoc'] = tarea_asoc_str
            # Intercambio de valores
            df.at[index, 'Tarea'], df.at[index, 'TareaAsoc'] = row['TareaAsoc'], row['Tarea']

    return df


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

