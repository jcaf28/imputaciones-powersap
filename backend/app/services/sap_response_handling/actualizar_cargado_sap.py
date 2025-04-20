# PATH: backend/app/services/sap_response_handling/actualizar_cargado_sap.py

from __future__ import annotations
import pandas as pd

from app.db.session import database_session
from app.models.models import TablaCentral, Imputaciones
from sqlalchemy import or_, func, true, false

def _clean_str(value) -> str | None:
    """
    Convierte a string, quita '.0' y espacios; devuelve None si NaN/None.
    """
    if pd.isna(value):
        return None
    return str(value).replace(".0", "").strip()


def _safe_float(value) -> float | None:
    """
    Convierte a float; devuelve None si NaN o conversion imposible.
    """
    try:
        return round(float(value), 2)
    except Exception:
        return None


def leer_datos_excel(path: str):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return df, True
    except Exception as e:
        print(f"[leer_datos_excel] Error: {e}")
        return None, False

# --------------------------------------------------------------------------
#                     FUNCIONES PRINCIPALES
# --------------------------------------------------------------------------
def actualizar_cargado_sap(df: pd.DataFrame) -> bool:
    """
    Marca `Cargado_SAP = True` para filas con estado **Success**.
    Las conversiones se adaptan a los tipos de la BD.
    """
    # ---------- Normalizaciones seguras ----------
    df.iloc[:, 0]  = df.iloc[:, 0].apply(_clean_str)          # Employee_Number → str
    df.iloc[:, 1]  = pd.to_datetime(df.iloc[:, 1], errors="coerce").dt.date  # Date
    df.iloc[:, 7]  = pd.to_numeric(df.iloc[:, 7], errors="coerce").astype("Int64")  # BIGINT
    df.iloc[:, 9]  = df.iloc[:, 9].apply(_clean_str)          # OperationActivity → str
    df.iloc[:, 10] = df.iloc[:, 10].apply(_safe_float)        # Hours

    total = success = actualizados = 0

    with database_session as db:
        for _, fila in df.iterrows():
            total += 1
            if fila.iloc[12] != "Success":
                continue

            success += 1

            query = (
                db.query(TablaCentral)
                .filter(
                    TablaCentral.Employee_Number   == fila.iloc[0],     # str
                    TablaCentral.Date              == fila.iloc[1],     # date
                    TablaCentral.ProductionOrder   == fila.iloc[7],     # BIGINT (int64)
                    TablaCentral.OperationActivity == fila.iloc[9],     # str
                    TablaCentral.Hours             == fila.iloc[10],    # float
                    TablaCentral.Cargado_SAP       == False,
                )
                .first()
            )

            if query:
                query.Cargado_SAP = True
                db.commit()
                actualizados += 1

    print(f"Total filas Excel           : {total}")
    print(f"Filas con estado 'Success'  : {success}")
    print(f"Registros actualizados en BD: {actualizados}")
    return True


def limpiar_registros() -> None:
    with database_session as db:
        # 1) borrar registros con Cargado_SAP = False
        eliminados_tc = (
            db.query(TablaCentral)
            .filter(TablaCentral.Cargado_SAP.is_(False))    # ← aquí
            .delete(synchronize_session="fetch")
        )
        print(f"Registros eliminados de Tabla_Central con Cargado_SAP=False: {eliminados_tc}")

        # 2) borrar imputaciones huérfanas
        subq = (
            db.query(Imputaciones.ID)
            .join(TablaCentral, Imputaciones.ID == TablaCentral.imputacion_id, isouter=True)
            .filter(or_(TablaCentral.ID == None, TablaCentral.Cargado_SAP.is_not(True)))  # ← aquí
            .group_by(Imputaciones.ID)
            .having(func.count(TablaCentral.ID) == 0)
            .subquery()
        )

        eliminados_imp = (
            db.query(Imputaciones)
            .filter(Imputaciones.ID.in_(subq))
            .delete(synchronize_session="fetch")
        )
        print(f"Imputaciones eliminadas sin registro válido: {eliminados_imp}")

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
