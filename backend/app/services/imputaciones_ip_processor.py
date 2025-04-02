# PATH: backend/app/services/imputaciones_ip_processor.py

import os
import asyncio
import uuid
from app.core.sse_manager import sse_manager

# Aquí tu logica real de ETL
from .imputaciones_ip.loader import cargar_y_limpiar_datos
from .imputaciones_ip.transformer import (
    generar_variables_negocio, generar_tabla_imputaciones, generar_cuadre_horas
)
from .imputaciones_ip.exporter import generar_csv_salida, generar_cuadre_xlsx

async def long_running_task(process_id: str, filepaths: list[str]):
    """
    Tarea que lee los 4 paths: (descarga_imputaciones, listado_usuarios, wbs_por_clave, fichajes_sap)
    y ejecuta la ETL real. Luego marca SSE completed, etc.
    """
    try:
        sse_manager.send_message(process_id, "Cargando y limpiando datos...")

        # Por ejemplo, asumiendo que filepaths está en el orden 0..3
        dfs = cargar_y_limpiar_datos(*filepaths)
        wbs_por_clave, listado_usuarios, descarga_imputaciones, fichajes_sap = dfs

        sse_manager.send_message(process_id, "Generando variables de negocio...")
        await asyncio.sleep(1)
        descarga_imputaciones, listado_usuarios, wbs_por_clave, fichajes_sap = generar_variables_negocio(
            descarga_imputaciones, listado_usuarios, wbs_por_clave, fichajes_sap
        )

        sse_manager.send_message(process_id, "Generando tabla de imputaciones...")
        await asyncio.sleep(1)
        horas_proyecto = generar_tabla_imputaciones(
            descarga_imputaciones, listado_usuarios, wbs_por_clave, fichajes_sap
        )

        sse_manager.send_message(process_id, "Generando cuadre de horas...")
        await asyncio.sleep(1)
        cuadre_horas = generar_cuadre_horas(descarga_imputaciones, fichajes_sap)

        sse_manager.send_message(process_id, "Exportando archivos finales...")
        await asyncio.sleep(1)

        # Generar CSV/Excel en /tmp
        output_subdir = f"/tmp/output_{process_id}"
        os.makedirs(output_subdir, exist_ok=True)

        generar_csv_salida(horas_proyecto, output_subdir)
        generar_cuadre_xlsx(cuadre_horas, output_subdir)

        # Podrías crear un ZIP con todos los ficheros
        # o quedarte con uno principal. Depende de tu necesidad.

        # Por ejemplo, guardamos un zip final:
        import shutil
        result_zip = f"/tmp/imputaciones_{process_id}.zip"
        shutil.make_archive(result_zip.replace(".zip",""), 'zip', output_subdir)

        sse_manager.mark_completed(process_id, "Proceso completado con éxito", result_file=result_zip)

    except Exception as e:
        sse_manager.mark_error(process_id, f"Error en la ETL: {str(e)}")
