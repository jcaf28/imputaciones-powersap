# PATH: backend/app/services/etl_inmemory/_load_datos_excel.py

import pandas as pd
from app.models.models import Extraciclos

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


def verificar_duplicados(df):
    # Asegurarse de que los NaN no afecten la agrupación, reemplazándolos con un valor temporal
    # Esto es opcional y depende de si esperas NaN en tus columnas clave
    # Si decides reemplazar NaN, asegúrate de usar un valor que no se encuentre en tus datos
    cols = ['CodEmpleado', 'FechaImp', 'Timpu', 'Horas', 'Proyecto', 'TipoCoche', 'NumCoche', 'CentroTrabajo', 'Tarea', 'TareaAsoc', 'TipoMotivo', 'TipoIndirecto']
    df_temp = df.fillna('ValorTemporalParaNaN')

    # Ahora realiza el conteo de duplicados
    df_temp['dup_count'] = df_temp.groupby(cols)['CodEmpleado'].transform('count')
    
    # Si has reemplazado NaN con un valor temporal y deseas restaurar los NaN originales en las columnas claves, hazlo aquí
    # Esto también es opcional y depende de tus necesidades
    # df[cols] = df[cols].replace('ValorTemporalParaNaN', np.nan)

    # Asegúrate de asignar el resultado correcto a tu DataFrame original si usaste un DataFrame temporal
    df['dup_count'] = df_temp['dup_count']

    return df


def existe_combinacion_area_tarea(centro_trabajo, tarea, session):
  return session.query(Extraciclos).filter(
      Extraciclos.CentroTrabajo == centro_trabajo,
      Extraciclos.TareaBaan == tarea
  ).first() is not None