# PATH: app/services/etl_inmemory/load_datos_excel_inmemory.py

def load_datos_excel_inmemory(df, db_session=None, sse_process_id=None, summary=None):
    """
    Procesa el DF, inserta en BD, anota Status y error_message en cada fila.
    Devuelve df_result con columns extra => 'Status', 'error_message'
    """
    import pandas as pd
    from datetime import datetime
    from sqlalchemy import func
    from sqlalchemy.exc import IntegrityError

    from app.db.session import database_session
    from app.models.models import Imputaciones
    from ._load_datos_excel import (
        verificar_duplicados,
        existe_combinacion_area_tarea
    )
    from app.core.sse_manager import sse_manager

    if summary is None:
        summary = {"total": len(df), "success": 0, "fail": 0}

    # Creamos dos columnas extra en df => 'Status' y 'error_message'
    df["Status"] = None
    df["error_message"] = None

    print("Cargando datos en BD... (inmemory)")
    if sse_process_id:
        sse_manager.send_message(sse_process_id, "📥 Preparando datos...")

    df=verificar_duplicados(df)

    nuevos_registros = 0
    errores = []

    session = db_session or database_session
    with session as db:
        for index, row in df.iterrows():
            try:
                existing_count = db.query(func.count(Imputaciones.ID)).filter(
                    Imputaciones.CodEmpleado == row.get('CodEmpleado'),
                    Imputaciones.FechaImp == row.get('FechaImp'),
                    Imputaciones.Timpu == row.get('Timpu'),
                    Imputaciones.Horas == row.get('Horas'),
                    Imputaciones.Proyecto == row.get('Proyecto'),
                    Imputaciones.TipoCoche == row.get('TipoCoche'),
                    Imputaciones.NumCoche == row.get('NumCoche'),
                    Imputaciones.CentroTrabajo == row.get('CentroTrabajo'),
                    Imputaciones.Tarea == row.get('Tarea'),
                    Imputaciones.TareaAsoc == row.get('TareaAsoc'),
                    Imputaciones.TipoMotivo == row.get('TipoMotivo'),
                    Imputaciones.TipoIndirecto == row.get('TipoIndirecto')
                ).scalar()

                wanted_count = int(row.get('dup_count', 1))

                if existing_count < wanted_count:
                    # Insertar
                    combinacion_valida = existe_combinacion_area_tarea(
                        row.get('CentroTrabajo'),
                        row.get('TareaAsoc'),
                        db
                    )
                    area_tarea = f"{row.get('CentroTrabajo')}-{row.get('TareaAsoc')}" if combinacion_valida else None

                    imputacion = Imputaciones(
                        CodEmpleado=row.get('CodEmpleado'),
                        FechaImp=row.get('FechaImp'),
                        Timpu=row.get('Timpu'),
                        Horas=row.get('Horas'),
                        Proyecto=row.get('Proyecto'),
                        TipoCoche=row.get('TipoCoche'),
                        NumCoche=row.get('NumCoche'),
                        CentroTrabajo=row.get('CentroTrabajo'),
                        Tarea=row.get('Tarea'),
                        TareaAsoc=row.get('TareaAsoc'),
                        area_id=row.get('CentroTrabajo'),
                        TipoMotivo=row.get('TipoMotivo'),
                        TipoIndirecto=row.get('TipoIndirecto'),
                        AreaTarea=area_tarea,
                        TipoImput=row.get('TipoImput')
                    )
                    db.add(imputacion)
                    db.commit()

                    nuevos_registros += 1
                    summary["success"] += 1
                    df.at[index, "Status"] = "OK"
                    df.at[index, "error_message"] = ""
                else:
                    df.at[index, "Status"] = "SKIPPED"
                    df.at[index, "error_message"] = f"Ya hay {existing_count} en BD, wanted={wanted_count}"
                    summary["fail"] += 1

            except IntegrityError as e:
                db.rollback()
                msg = f"error de integridad ({str(e.orig).splitlines()[0]})"
                errores.append(f"Fila {index+2}: {msg}")
                summary["fail"] += 1
                df.at[index, "Status"] = "FAIL"
                df.at[index, "error_message"] = msg
                if sse_process_id:
                    sse_manager.send_message(sse_process_id, f"❌ Fila {index+2}: {msg}")

            except Exception as e:
                db.rollback()
                msg = f"error inesperado: {str(e)}"
                errores.append(f"Fila {index+2}: {msg}")
                summary["fail"] += 1
                df.at[index, "Status"] = "FAIL"
                df.at[index, "error_message"] = msg
                if sse_process_id:
                    sse_manager.send_message(sse_process_id, f"❌ Fila {index+2}: {msg}")

    print(f"Proceso finalizado. Nuevos registros: {nuevos_registros}")
    if sse_process_id:
        sse_manager.send_message(sse_process_id, f"🟢 Insertados {nuevos_registros} nuevos registros.")

    if errores:
        print("Se encontraron errores:")
        for err in errores:
            print(err)

    return df  # ← devolvemos el DataFrame con las columnas Status / error_message
