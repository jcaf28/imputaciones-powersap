# PATH: backend/app/services/sap_etl_utils.py

import pandas as pd
from app.models.models import SapOrders
from sqlalchemy.orm import Session

def verificar_columnas_excel(df: pd.DataFrame, columnas_necesarias: list):
    """
    Lanza ValueError si no se encuentran las columnas obligatorias en el DataFrame.
    """
    for col in columnas_necesarias:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida '{col}' en el Excel")

def transformar_datos_sap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduce la lógica de b_transform.py pero en memoria.
    """
    # Ejemplo simplificado de las transformaciones que hacías:
    df['OperationActivityFull'] = df['Operation Activity']
    df['EffectivityFull'] = df['Effectivity']
    # Este parseo es un ejemplo del original:
    df['Order'] = pd.to_numeric(df['Order'].str.extract(r'\((\d+)\)')[0], errors='coerce')

    df['Operation'] = df['Operation Activity'].str.extract(r'(\d+)')
    df['OperationActivity'] = df['Operation Activity'].str.extract(r'^(\S+)')
    df['Description'] = df['Operation Activity'].str.extract(r'\((.*?)\)')

    df['Project'] = df['Effectivity'].str.extract(r'([A-Z]{2})(\d+)\.')[1]
    df['Area'] = df['Effectivity'].str.extract(r'\.\s*([A-Z]+)\.')[0]
    df['Vertice'] = df['Effectivity'].str.extract(r'([A-Z]+)\.([A-Z]),')[1]
    df['CarNumber'] = pd.to_numeric(df['Effectivity'].str.extract(r',(\d+)')[0], errors='coerce')

    df['TipoIndirecto'] = None
    df['TipoMotivo'] = None
    df['ActiveOrder'] = 1

    df['TipoTarea'] = df['OperationActivity'].apply(
        lambda x: (
            x[-2:] if isinstance(x, str) and x[-2:] in ['GG','XX','C0','C1','C2','C3']
            else 'XX' if isinstance(x, str) and x[-2:] == 'KI'
            else None
        )
    )

    columnas_modelo = [
        'OperationActivityFull', 'EffectivityFull', 'Order', 'Operation',
        'OperationActivity', 'Description', 'Project', 'Area', 'Vertice',
        'CarNumber', 'TipoIndirecto', 'TipoMotivo','TipoTarea','ActiveOrder'
    ]
    return df[columnas_modelo]

def cargar_datos_sap_en_db(df: pd.DataFrame, db_session: Session):
    """
    Inserta en SAPOrders los registros que no existan (basado en la tupla
    (OperationActivity, EffectivityFull, Order)).
    """
    # Asegurarnos de que 'Order' sea str en la DB
    df['Order'] = df['Order'].astype(str)

    # Obtenemos las combinaciones que ya existen en BD
    existentes = db_session.query(
        SapOrders.OperationActivity,
        SapOrders.EffectivityFull,
        SapOrders.Order
    ).all()

    existentes_set = set((op, eff, order) for op, eff, order in existentes)
    
    # Convertir a lista de dicts
    dict_rows = df.to_dict(orient='records')

    # Filtrar filas nuevas
    nuevos_registros = []
    for row in dict_rows:
        combo = (row['OperationActivity'], row['EffectivityFull'], row['Order'])
        if combo not in existentes_set:
            # Limpieza de NaNs
            clean_row = {
                k: (None if pd.isna(v) else v)
                for k, v in row.items()
            }
            nuevos_registros.append(clean_row)

    if nuevos_registros:
        db_session.bulk_insert_mappings(SapOrders, nuevos_registros)
        db_session.commit()
        print(f"Insertados {len(nuevos_registros)} registros nuevos en SAPOrders.")
    else:
        print("No hay registros nuevos para insertar.")
