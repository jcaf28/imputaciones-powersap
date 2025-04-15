# PATH: backend/app/services/generar_imputaciones_sap/generar_csv.py

# PATH: backend/app/services/generar_imputaciones_sap/generar_csv.py

import os
import csv
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import TablaCentral

def fetch_data(db: Session) -> pd.DataFrame:
    """
    Retorna un DataFrame con las filas de TablaCentral donde Cargado_SAP == False.
    """
    query = db.query(
        TablaCentral.Employee_Number,
        TablaCentral.Date,
        TablaCentral.HourType,
        TablaCentral.ProductionOrder,
        TablaCentral.Operation,
        TablaCentral.OperationActivity,
        TablaCentral.Hours
    ).filter(TablaCentral.Cargado_SAP == False)

    df = pd.read_sql(query.statement, db.bind)
    return df

def format_date(date):
    """
    Devuelve la fecha en formato dd/mm/YYYY o vacío si es nulo.
    """
    return date.strftime("%d/%m/%Y") if pd.notnull(date) else ""

def map_hourtype(op_act, original_hourtype):
    """
    Lógica de mapeo:
     - Si OperationActivity acaba en 'XX' => 3
     - Si acaba en 'GG' => 4
     - Si acaba en 'C...' => 5
     - En otro caso => original_hourtype
    """
    if isinstance(op_act, str):
        if op_act.endswith("XX"):
            return 3
        if op_act.endswith("GG"):
            return 4
        # Si p.ej 'C2', 'C3', etc. => 
        # (comprobamos que al menos los 2 últimos chars contengan 'C', 
        #  EJEMPLO: 'OPC2' -> endswith('C2') => True)
        if len(op_act) >= 2 and op_act[-2] == "C":
            return 5
    return original_hourtype

def generate_csv_file(db: Session) -> str:
    """
    Genera un CSV a partir de las filas con Cargado_SAP=False y
    devuelve la ruta donde se guardó.
    """
    data = fetch_data(db)
    if data.empty:
        # Retorna un CSV vacío si no hay nada
        # (o podríamos devolver None para indicar que no hay nada)
        pass

    # 1) Formatear la columna Date
    data['Date'] = data['Date'].apply(format_date)

    # 2) Añadir columnas extra con valor vacío
    for col in ['Project', 'Wbs', 'Cost Center', 'Activity Type', 'Status', 'Serial Number']:
        data[col] = ''

    # 3) Ajustar HourType según la OperationActivity
    data['HourType'] = [
        map_hourtype(act, ht) for act, ht in zip(data['OperationActivity'], data['HourType'])
    ]

    # 4) Reordenar columnas
    columnas_finales = [
        'Employee_Number',
        'Date',
        'HourType',
        'Project',
        'Wbs',
        'Cost Center',
        'Activity Type',
        'ProductionOrder',
        'Operation',
        'OperationActivity',
        'Hours',
        'Status',
        'Serial Number'
    ]
    data = data[columnas_finales]

    # 5) Guardar en una carpeta temporal
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"mass_upload_{timestamp}.csv"
    tmp_dir = os.path.join(os.getcwd(), "tmp_csv_sap")  # Ajusta la carpeta como prefieras
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    csv_path = os.path.join(tmp_dir, file_name)

    # 6) Exportar CSV con separador ';', codificación cp1252 y lineterminator '\r\n'
    data.to_csv(
        csv_path,
        sep=';',
        encoding='cp1252',
        index=False,
        lineterminator='\r\n',
        quoting=csv.QUOTE_MINIMAL
    )

    return csv_path
