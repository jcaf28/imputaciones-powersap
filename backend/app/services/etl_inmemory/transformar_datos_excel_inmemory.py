# PATH: app/services/etl_inmemory/transformar_datos_excel_inmemory.py

def transformar_datos_excel_inmemory(df):
    import pandas as pd
    import numpy as np
    from app.db.session import database_session
    from app.models.models import Extraciclos

    print("Datos cargados a df (inmemory). Comenzando transformaciones...")

    # 1) Filtros / limpiezas (ejemplo)
    if 'Factoria' in df.columns:
        df = df[df['Factoria'] == 'Div3']

    if 'Fecha' in df.columns and 'FechaImp' not in df.columns:
        df = df.rename(columns={'Fecha': 'FechaImp'})

    if 'Comentario' in df.columns:
        df['Comentario'] = df['Comentario'].astype(str)
        df = df[~(df['Comentario'].str.contains('FU', na=False) & df['Comentario'].str.contains('300', na=False))]

    df = df.replace([np.nan, 'nan', 'NAN', 'none', 'NONE'], None)

    # Por ejemplo, si la columna 'Tarea' == '3986', convertir a '3060'
    if 'Tarea' in df.columns:
        mask_tarea_3986 = df['Tarea'] == '3986'
        df.loc[mask_tarea_3986, 'Tarea'] = '3060'

    # Ejemplo de merges con Extraciclos
    with database_session as db:
        extraciclos = db.query(Extraciclos).all()

    if extraciclos:
        extraciclos_df = pd.DataFrame([
            {'AreaTarea': e.AreaTarea, 'TipoCNC': e.TipoCNC} for e in extraciclos
        ])
        # etc. Haz merges y reasignaciones como en tu script original

    print("Transformaciones completadas (inmemory).")
    return df
