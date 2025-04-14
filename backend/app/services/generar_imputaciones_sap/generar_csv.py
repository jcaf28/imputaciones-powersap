# PATH: backend/app/services/generar_imputaciones_sap/generar_csv.py

import os
import subprocess
from datetime import datetime
import pandas as pd
import csv

from app.db.session import database_session
from app.models.models import TablaCentral

def fetch_data() -> pd.DataFrame:
    """
    Consulta TablaCentral para obtener registros con Cargado_SAP=False.
    Devuelve un DataFrame con las columnas requeridas.
    """
    print("Iniciando la consulta de datos en TablaCentral (Cargado_SAP=False)...")
    with database_session as db:
        query = db.query(
            TablaCentral.Employee_Number,
            TablaCentral.Date,
            TablaCentral.HourType,
            TablaCentral.ProductionOrder,
            TablaCentral.Operation,
            TablaCentral.OperationActivity,
            TablaCentral.Hours
        ).filter(TablaCentral.Cargado_SAP == False)

        data = pd.read_sql(query.statement, db.bind)

    print(f"Datos obtenidos: {len(data)} registros")
    return data

def format_date(date_val):
    """
    Devuelve la fecha en formato dd/mm/yyyy si no es nulo,
    o cadena vacía en caso contrario.
    """
    if pd.notnull(date_val):
        return date_val.strftime('%d/%m/%Y')
    return ''

def generate_excel():
    """
    Genera dos archivos en la ruta S:\\O-BEA-14-DIVISION_3\\Eider\\Mass Upload:
      1) Un Excel mass_upload_YYYYmmdd_HHMMSS.xlsx
      2) Un CSV mass_upload_YYYYmmdd_HHMMSS.csv (separador ';')
    con la misma información, formateada para SAP/Excel.

    Si no deseas guardarlos en disco, podrías:
      - Generar ambos en memoria (BytesIO) y servirlos directamente.
      - Borrarlos tras su uso.
    """
    print("Generando el archivo Excel/CSV para imputaciones pendientes...")

    # 1) Cargar los datos de TablaCentral (Cargado_SAP=False)
    data = fetch_data()

    # 2) Formatear la columna de fecha
    data['Date'] = data['Date'].apply(format_date)

    # 3) Crear columnas faltantes
    for col in ['Project', 'Wbs', 'Cost Center', 'Activity Type', 'Status', 'Serial Number']:
        data[col] = ''

    # 4) Ajustar HourType según OperationActivity
    def map_hourtype(op_act, original_hourtype):
        """
        Lógica especial de etiquetado:
          - Si op_act termina en "XX" => 3
          - Si op_act termina en "GG" => 4
          - Si penúltimo char es "C" => 5
          - Caso contrario, se deja original
        """
        if isinstance(op_act, str):
            if op_act.endswith("XX"):
                return 3
            elif op_act.endswith("GG"):
                return 4
            elif len(op_act) >= 2 and op_act[-2] == "C":
                return 5
        return original_hourtype

    data['HourType'] = [
        map_hourtype(act, ht) for act, ht in zip(data['OperationActivity'], data['HourType'])
    ]

    # 5) Reordenar columnas
    columnas_finales = [
        'Employee_Number', 'Date', 'HourType', 'Project', 'Wbs', 'Cost Center',
        'Activity Type', 'ProductionOrder', 'Operation', 'OperationActivity',
        'Hours', 'Status', 'Serial Number'
    ]
    data = data[columnas_finales]

    # 6) Directorio de salida
    dir_path = r"S:\O-BEA-14-DIVISION_3\Eider\Mass Upload"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # 7) Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"mass_upload_{timestamp}"
    xlsx_path = os.path.join(dir_path, file_name + ".xlsx")
    csv_path = os.path.join(dir_path, file_name + ".csv")

    # 8) Guardar Excel
    print(f"Guardando archivo Excel en: {xlsx_path}")
    with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Report')
    print("Archivo Excel generado con éxito.")

    # 9) Guardar CSV en formato SAP/Excel (usando ';', cod cp1252)
    print(f"Guardando archivo CSV en: {csv_path}")
    data.to_csv(
        csv_path,
        sep=';',
        encoding='cp1252',
        index=False,
        lineterminator='\r\n',
        quoting=csv.QUOTE_MINIMAL
    )
    print("Archivo CSV generado con éxito.")

    # 10) (Opcional) abrir la carpeta en Explorador
    subprocess.run(f'explorer /select,\"{xlsx_path}\"', shell=True)

if __name__ == "__main__":
    generate_excel()