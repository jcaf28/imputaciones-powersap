# PATH: backend/app/services/etl_inmemory/transformar_datos_excel_inmemory.py

def transformar_datos_excel_inmemory(df):
    import pandas as pd
    import numpy as np
    from app.db.session import database_session
    from app.models.models import Extraciclos

    print("Datos cargados a df (inmemory). Comenzando transformaciones...")

    # ----------------------------------------------------------------------
    # 1) Filtros y limpiezas iniciales
    # ----------------------------------------------------------------------
    if 'Factoria' in df.columns:
        df = df[df['Factoria'] == 'Div3']

    if 'Fecha' in df.columns and 'FechaImp' not in df.columns:
        df = df.rename(columns={'Fecha': 'FechaImp'})

    # Aquí forzamos dd/mm/yyyy => date
    if 'FechaImp' in df.columns:
        df['FechaImp'] = pd.to_datetime(df['FechaImp'], dayfirst=True, errors='coerce').dt.date

    if 'Comentario' in df.columns:
        # Convertir a str para usar .contains()
        df['Comentario'] = df['Comentario'].astype(str)
        # Filtro: elimina SOLO filas que contengan AMBOS 'FU' y '300'
        df = df[~(df['Comentario'].str.contains('FU') & df['Comentario'].str.contains('300'))]

    if 'TipoMotivo' in df.columns:
        df['TipoMotivo'] = df['TipoMotivo'].str.lstrip('0')

    # TipoIndirecto ya es str desde dtype=str

    # Quitar 'PERMISOS'
    if 'Proyecto' in df.columns:
        df = df.loc[df['Proyecto'] != 'PERMISOS']

    # Sustituir valores como np.nan, 'nan', 'NAN', etc. por None
    df = df.replace([np.nan, 'nan', 'NAN', 'none', 'NONE'], None)
    df = df.where(pd.notna(df), None)

    # Tronchar 'CentroTrabajo' a 3 chars si existe
    if 'CentroTrabajo' in df.columns:
        df['CentroTrabajo'] = df['CentroTrabajo'].apply(lambda x: str(x)[:3] if x else x)

    # ----------------------------------------------------------------------
    # 2) Modificaciones ad hoc
    # ----------------------------------------------------------------------
    if 'Tarea' in df.columns:
        # Si 'Tarea' == '3986', cambiar a '3060'
        mask_tarea_3986 = df['Tarea'] == '3986'
        df.loc[mask_tarea_3986, 'Tarea'] = '3060'

    # ----------------------------------------------------------------------
    # 3) Asignar columna 'TipoImput' según reglas
    # ----------------------------------------------------------------------
    df['TipoImput'] = None

    # (3.1) Gasto General => 'GG'
    if 'Proyecto' in df.columns:
        mask_gg = (df['Proyecto'] == 'Gasto General')
        df.loc[mask_gg, 'TipoImput'] = 'GG'

    # (3.2) ExtraCiclos => usar 'TipoCNC' si coincide con 'AreaTarea'
    if 'CentroTrabajo' in df.columns and 'TareaAsoc' in df.columns:
        df['AreaTarea'] = df.apply(
            lambda row: f"{row['CentroTrabajo']}-{row['TareaAsoc']}"
            if row['CentroTrabajo'] and row['TareaAsoc']
            else None,
            axis=1
        )

    with database_session as db:
        extraciclos = db.query(Extraciclos).all()

    if extraciclos:
        extraciclos_df = pd.DataFrame([
            {'AreaTarea': e.AreaTarea, 'TipoCNC': e.TipoCNC} for e in extraciclos
        ])
    else:
        extraciclos_df = pd.DataFrame()

    if not extraciclos_df.empty and 'AreaTarea' in df.columns:
        merged = df.merge(extraciclos_df, on='AreaTarea', how='left')
        cond_tipoimput_null = merged['TipoImput'].isna()
        cond_tipocnc_notnull = merged['TipoCNC'].notna()
        merged.loc[cond_tipoimput_null & cond_tipocnc_notnull, 'TipoImput'] = (
            merged.loc[cond_tipoimput_null & cond_tipocnc_notnull, 'TipoCNC']
        )
        df = merged.drop(columns=['TipoCNC'])
    else:
        print("No hay registros en Extraciclos o no existe 'AreaTarea'.")

    # (3.3) Caso 'XX': TipoImput sigue None, y (TareaAsoc, TipoIndirecto, TipoMotivo) = None
    cond_tipoimput_null = df['TipoImput'].isna()
    cond_tareaasoc_null = ('TareaAsoc' in df.columns) and df['TareaAsoc'].isna()
    cond_tipomot_null   = ('TipoMotivo' in df.columns) and df['TipoMotivo'].isna()
    cond_tipoin_null    = ('TipoIndirecto' in df.columns) and df['TipoIndirecto'].isna()
    if isinstance(cond_tareaasoc_null, pd.Series):
        mask_xx = cond_tipoimput_null & cond_tareaasoc_null & cond_tipomot_null & cond_tipoin_null
        df.loc[mask_xx, 'TipoImput'] = 'XX'

    # ----------------------------------------------------------------------
    # 4) Limpieza según "TipoImput"
    # ----------------------------------------------------------------------
    # Si TipoImput != 'GG' y 'TipoCoche' es None => eliminar la fila
    if 'TipoCoche' in df.columns:
        mask_tipoimput_notgg = df['TipoImput'] != 'GG'
        mask_tipocoche_null = df['TipoCoche'].isna()
        df = df[~(mask_tipoimput_notgg & mask_tipocoche_null)]

    # ----------------------------------------------------------------------
    # 5) Intercambiar valores Tarea <-> TareaAsoc
    #    HAZLO AQUÍ, antes de convertir a str, para que la condición sea más limpia
    # ----------------------------------------------------------------------
    if 'TareaAsoc' in df.columns and 'Tarea' in df.columns:
        for index, row in df.iterrows():
            # TareaAsoc está como None (o int/float si venía del Excel)
            # Verificamos si es un valor real
            if row['TareaAsoc'] is not None and str(row['TareaAsoc']).strip() != '':
                # Intercambio
                old_tarea = row['Tarea']
                df.at[index, 'Tarea']    = row['TareaAsoc']
                df.at[index, 'TareaAsoc'] = old_tarea

    # ----------------------------------------------------------------------
    # 6) Conversión de tipos numéricos
    # ----------------------------------------------------------------------
    # Con dtype=str en read_excel, todos los campos ya son str.
    # Solo necesitamos convertir Horas a numérico.
    if 'Horas' in df.columns:
        df['Horas'] = pd.to_numeric(df['Horas'], errors='coerce').round(2)

    # ----------------------------------------------------------------------
    # 7) Paso final: re-convertir strings tipo 'None', 'nan', etc. a None real
    # ----------------------------------------------------------------------
    df.replace(
        to_replace=['nan', 'NaN', 'NAN', 'None', 'NONE', 'null', 'NULL'],
        value=None,
        inplace=True
    )
    # Donde haya np.nan, pásalo a None
    df.where(pd.notna(df), None, inplace=True)

    print("Transformaciones completadas (inmemory).")
    return df
