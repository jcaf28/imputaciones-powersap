# PATH: backend/app/services/seguimiento_escaneos_service.py

import os
import pandas as pd
from datetime import datetime
import asyncio
from app.core.sse_manager import sse_manager

# Ajusta la ruta de import a tus utilidades reales:
from .utils.escaneos_utils import (
    obtener_nombres_pdf,
    aplicar_estilos_excel,
    procesar_dataframe_encontrados,
)

async def process_escaneos_logic(process_id: str, file_location: str) -> str:
    """
    Lógica real de seguimiento de escaneos, pero enviando mensajes SSE al frontend
    en cada punto clave. 
    - Lee el Excel subido (file_location).
    - Busca PDFs en la ruta DIRECTORIO_PDFS (definida en .env o por defecto).
    - Genera un .xlsx final (almacenado en /tmp).
    - Va notificando cada paso mediante SSE.

    Devuelve la ruta del archivo final .xlsx para que luego /download/{process_id}
    lo sirva al frontend.
    """

    # Lee la ruta de PDFs desde la variable de entorno (definida en .env o en Docker).
    pdf_directory = os.getenv(
        "DIRECTORIO_PDFS",
        r"/tmp/pdfs"  # Valor por defecto si no existe la var en .env
    )

    # 1) Notificamos que empieza el proceso
    sse_manager.send_message(process_id, "Iniciando proceso de seguimiento de escaneos...")
    await asyncio.sleep(1)

    # 2) Obtener nombres de PDF
    sse_manager.send_message(process_id, "Obteniendo nombres de archivos PDF...")
    await asyncio.sleep(1)
    pdfs = obtener_nombres_pdf(pdf_directory)
    pdf_dict = {
        nombre.split('.', 1)[0].strip('() '): ruta for (nombre, ruta) in pdfs
    }
    sse_manager.send_message(
        process_id,
        f"Encontrados {len(pdfs)} PDF(s). Procesando coincidencias..."
    )
    await asyncio.sleep(1)

    # Verificamos si está cancelado antes de avanzar
    state = sse_manager.get_state(process_id)
    if state and state["cancelled"]:
        sse_manager.send_message(process_id, "Proceso cancelado antes de leer Excel.")
        await asyncio.sleep(1)
        return ""

    # 3) Leer el Excel subido
    sse_manager.send_message(process_id, f"Leyendo archivo Excel: {file_location}")
    await asyncio.sleep(1)
    df_xlsx = pd.read_excel(file_location)

    # 4) Crear la columna Key e indexar
    df_xlsx['Key'] = (
        df_xlsx['Order'].astype(str).str.strip('() ')
        + '-'
        + df_xlsx['Operation Activity'].astype(str).str.split('-', n=1).str[0].str.strip()
    )
    xlsx_dict = df_xlsx.set_index('Key').T.to_dict('list')

    # 5) Buscar coincidencias entre PDFs y XLSX
    sse_manager.send_message(process_id, "Buscando coincidencias entre PDFs y XLSX...")
    await asyncio.sleep(1)

    encontrados = []
    no_encontrados = []

    for key, pdf_ruta in pdf_dict.items():
        if key in xlsx_dict:
            data = xlsx_dict[key]
            data.append(pdf_ruta)  # Añadimos ruta PDF a la lista
            encontrados.append(data)
        else:
            no_encontrados.append({'Key': key, 'UbicacionPDF': pdf_ruta})

    # 6) Construir DataFrames
    expected_columns = [
        'Operation Activity',
        'OA Status',
        'Order',
        'Material',
        'Effectivity',
        'OA SFI Status',
        'UbicacionPDF'
    ]
    df_encontrados = pd.DataFrame(encontrados, columns=expected_columns)
    df_no_encontrados = pd.DataFrame(no_encontrados)

    df_encontrados = procesar_dataframe_encontrados(df_encontrados)

    # Verificar si está cancelado antes de guardar
    state = sse_manager.get_state(process_id)
    if state and state["cancelled"]:
        sse_manager.send_message(process_id, "Proceso cancelado antes de generar archivo final.")
        await asyncio.sleep(1)
        return ""

    # 7) Guardar el archivo final en /tmp
    sse_manager.send_message(process_id, "Guardando archivo actualizado en /tmp...")
    await asyncio.sleep(1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"seguimiento_escaneos_{timestamp}.xlsx"
    ruta_guardado = os.path.join("/tmp", nombre_archivo)

    with pd.ExcelWriter(ruta_guardado, engine='openpyxl') as writer:
        df_encontrados.to_excel(writer, index=False, sheet_name='Encontrados')
        df_no_encontrados.to_excel(writer, index=False, sheet_name='No Encontradas')

    # 8) Aplicar estilos (columnas autoajustadas, colores, etc.)
    aplicar_estilos_excel(ruta_guardado)

    sse_manager.send_message(process_id, f"Archivo generado con éxito: {ruta_guardado}")
    await asyncio.sleep(1)

    # 9) Devolver la ruta final para que el endpoint /download/{process_id} la sirva
    return ruta_guardado
