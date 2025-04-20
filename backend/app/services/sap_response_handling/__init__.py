# PATH: backend/app/services/sap_response_handling/__init__.py

from __future__ import annotations
import pandas as pd

from app.db.session import database_session
from app.models.models import TablaCentral, Imputaciones
from sqlalchemy import or_, func

# --------------------------------------------------------------------------
#                     FUNCIONES PRINCIPALES
# --------------------------------------------------------------------------
def leer_datos_excel(archivo):
    try:
        return pd.read_excel(archivo), True
    except Exception as e:
        print(f"Error al cargar el archivo Excel: {e}")
        return None, False
    
def actualizar_cargado_sap(registros_excel: pd.DataFrame) -> bool:
    """
    Recorre el DataFrame de la respuesta SAP y marca como `Cargado_SAP = True`
    aquellos registros que coincidan y estén en estado **Success**.
    """
    # Normalizaciones de tipo
    registros_excel.iloc[:, 1]  = pd.to_datetime(registros_excel.iloc[:, 1]).dt.date     # Date
    registros_excel.iloc[:, 7]  = registros_excel.iloc[:, 7].astype("int64")             # Order
    registros_excel.iloc[:, 9]  = (
        registros_excel.iloc[:, 9].astype(str).str.replace(".0", "", regex=False)
    )  # Operation Activity
    registros_excel.iloc[:, 10] = registros_excel.iloc[:, 10].astype(float).round(2)     # Hours

    total_registros        = 0
    registros_success      = 0
    registros_actualizados = 0

    with database_session as db:
        for _, fila in registros_excel.iterrows():
            total_registros += 1

            # Columna 12 contiene el estado (Success / Error / …)
            if fila.iloc[12] == "Success":
                registros_success += 1

                query = (
                    db.query(TablaCentral)
                    .filter(
                        TablaCentral.Employee_Number   == fila.iloc[0],
                        TablaCentral.Date              == fila.iloc[1],
                        TablaCentral.ProductionOrder   == fila.iloc[7],
                        TablaCentral.OperationActivity == fila.iloc[9],
                        TablaCentral.Hours             == fila.iloc[10],
                        TablaCentral.Cargado_SAP       == False,
                    )
                    .first()
                )

                if query:
                    query.Cargado_SAP = True
                    db.commit()
                    registros_actualizados += 1

    print(f"Total de registros analizados: {total_registros}")
    print(f"Registros con 'Success'     : {registros_success}")
    print(f"Total de registros actualizados: {registros_actualizados}")
    return True


def limpiar_registros() -> None:
    """
    Elimina de la BD los registros huérfanos o marcados como no cargados.
    """
    with database_session as db:
        # 1) TablaCentral donde Cargado_SAP = 0
        eliminados_tc = (
            db.query(TablaCentral).filter_by(Cargado_SAP=0).delete(synchronize_session="fetch")
        )
        print(f"Registros eliminados de Tabla_Central con Cargado_SAP=0: {eliminados_tc}")

        # 2) Imputaciones sin vínculo con TablaCentral válida
        subq = (
            db.query(Imputaciones.ID)
            .join(TablaCentral, Imputaciones.ID == TablaCentral.imputacion_id, isouter=True)
            .filter(or_(TablaCentral.ID == None, TablaCentral.Cargado_SAP != 1))
            .group_by(Imputaciones.ID)
            .having(func.count(TablaCentral.ID) == 0)
            .subquery()
        )

        eliminados_imp = (
            db.query(Imputaciones).filter(Imputaciones.ID.in_(subq)).delete(synchronize_session="fetch")
        )
        print(
            "Imputaciones eliminadas sin registro en Tabla_Central con Cargado_SAP=1:"
            f" {eliminados_imp}"
        )

        db.commit()


def procesar_respuesta_sap(archivo_excel: str) -> bool:
    """
    Punto de entrada único usado por la ruta SSE.  
    Devuelve *True* si todo fue bien, *False* en caso contrario.
    """
    registros_excel, ok = leer_datos_excel(archivo_excel)
    if not ok:
        print("Error al cargar el archivo de Excel.")
        return False

    if actualizar_cargado_sap(registros_excel):
        limpiar_registros()
        print("Proceso completado correctamente.")
        return True

    print("Error en la actualización de datos.")
    return False
