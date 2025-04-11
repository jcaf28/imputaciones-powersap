# PATH: app/services/etl_inmemory/load_datos_excel_inmemory.py

def load_datos_excel_inmemory(df, db_session=None, sse_process_id=None):
    import pandas as pd
    from datetime import datetime
    from sqlalchemy import func
    from sqlalchemy.exc import IntegrityError

    from app.db.session import database_session
    from app.models.models import Imputaciones
    from ._load_datos_excel import (
        intercambiar_tareas,
        verificar_duplicados,
        change_dtypes,
        existe_combinacion_area_tarea
    )
    from app.core.sse_manager import sse_manager

    print("Cargando datos en BD... (inmemory)")
    if sse_process_id:
        sse_manager.send_message(sse_process_id, "📥 Preparando datos...")

    # 1) Conversión de fecha + filtrado de futuros
    if 'FechaImp' in df.columns:
        df['FechaImp'] = pd.to_datetime(df['FechaImp'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['FechaImp'])
        df = df[df['FechaImp'] <= pd.to_datetime(datetime.now().date())]

    # 2) Ajustar dtypes, quitar duplicados, etc.
    df = change_dtypes(df)
    df = df.replace('None', None)
    df = intercambiar_tareas(df)
    df = verificar_duplicados(df)  # ← crea la columna 'dup_count'
    df = df.replace('None', None)

    nuevos_registros = 0
    errores = []

    session = db_session or database_session
    with session as db:
        for index, row in df.iterrows():
            try:
                # Contar cuántos registros idénticos hay en BD
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

                # Cuántas veces Excel dice que aparece: 'dup_count'
                # (ya calculado en verificar_duplicados)
                wanted_count = int(row.get('dup_count', 1))

                if existing_count < wanted_count:
                    # Nos faltan (wanted_count - existing_count) filas para igualar
                    # Pero insertamos "de una en una" cada vez que se ejecute esta fila
                    # => Insertar 1 más
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

                    # print(f"✅ Fila {index+2}: insertada (existing_count={existing_count}, wanted_count={wanted_count}).")
                else:
                    # existing_count >= wanted_count
                    if sse_process_id:
                        sse_manager.send_message(sse_process_id, f"⚠️ Fila {index+2}: ya hay {existing_count} en BD y Excel pide {wanted_count}, no se inserta.")

            except IntegrityError as e:
                db.rollback()
                error_msg = f"❌ Fila {index+2}: error de integridad ({str(e.orig).splitlines()[0]})"
                # print(error_msg)
                errores.append(error_msg)
                if sse_process_id:
                    sse_manager.send_message(sse_process_id, error_msg)

            except Exception as e:
                db.rollback()
                error_msg = f"❌ Fila {index+2}: error inesperado ({str(e)})"
                print(error_msg)
                errores.append(error_msg)
                if sse_process_id:
                    sse_manager.send_message(sse_process_id, error_msg)

    print(f"Proceso finalizado. Nuevos registros: {nuevos_registros}")
    if sse_process_id:
        sse_manager.send_message(sse_process_id, f"🟢 Insertados {nuevos_registros} nuevos registros.")

    if errores:
        print("Se encontraron errores:")
        for err in errores:
            print(err)

    return nuevos_registros
