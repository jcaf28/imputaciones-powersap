# PATH: backend/app/services/generar_imputaciones_sap/generar_csv.py

import os
import csv
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import TablaCentral
from zipfile import ZipFile

def fetch_data(db: Session) -> pd.DataFrame:
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
    return date.strftime("%d/%m/%Y") if pd.notnull(date) else ""

def map_hourtype(op_act, original_hourtype):
    if isinstance(op_act, str):
        if op_act.endswith("XX"):
            return 3
        if op_act.endswith("GG"):
            return 4
        if len(op_act) >= 2 and op_act[-2] == "C":
            return 5
    return original_hourtype

def generate_zip_with_csv_and_xlsx(db: Session) -> str:
    data = fetch_data(db)
    if data.empty:
        return None  # No hay filas => devolvemos None

    # 1) Formatear la columna 'Date'
    data['Date'] = data['Date'].apply(format_date)

    # 2) Añadir columnas extra
    for col in ['Project', 'Wbs', 'Cost Center', 'Activity Type', 'Status', 'Serial Number']:
        data[col] = ''

    # 3) Ajustar HourType según OperationActivity
    data['HourType'] = [
        map_hourtype(a, h) for a, h in zip(data['OperationActivity'], data['HourType'])
    ]

    # 3 bis) Añadir comilla simple en campos sensibles (para el CSV)
    data_csv = data.copy()
    for col in ['ProductionOrder', 'Operation', 'OperationActivity']:
        data_csv[col] = data_csv[col].apply(lambda x: f"'{x}" if pd.notnull(x) else '')

    # 4) Reordenar columnas
    cols_final = [
        'Employee_Number','Date','HourType','Project','Wbs','Cost Center',
        'Activity Type','ProductionOrder','Operation','OperationActivity',
        'Hours','Status','Serial Number'
    ]
    data_csv = data_csv[cols_final]
    data_xlsx = data[cols_final]

    # 5) Generar rutas
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"mass_upload_{timestamp}"
    tmp_dir = os.path.join(os.getcwd(), "tmp_csv_sap")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    csv_path = os.path.join(tmp_dir, base_name + ".csv")
    xlsx_path = os.path.join(tmp_dir, base_name + ".xlsx")
    zip_path = os.path.join(tmp_dir, base_name + ".zip")

    # 6) Guardar CSV
    data_csv.to_csv(
        csv_path, sep=';', encoding='cp1252',
        index=False, lineterminator='\r\n',
        quoting=csv.QUOTE_MINIMAL
    )

    # 7) Guardar XLSX
    data_xlsx.to_excel(
        xlsx_path, index=False
    )

    # 8) Crear el ZIP con ambos archivos
    with ZipFile(zip_path, 'w') as z:
        z.write(csv_path, arcname=os.path.basename(csv_path))
        z.write(xlsx_path, arcname=os.path.basename(xlsx_path))

    return zip_path
