# PATH: backend/app/services/cnc_processor.py

import os
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
import asyncio

from app.core.sse_manager import sse_manager
from .utils.cnc_processor_utils import (
    encontrar_archivo_mas_reciente,
    extraer_avisos_de_calidad,
    ordenar_registros,
    aplicar_formato,
    aplicar_formato_condicional
)

# ========== FUNCIÓN PRINCIPAL DE PROCESADO ==========

async def process_cnc_logic(process_id: str, user_file: str) -> str:
    """
    Lógica principal de procesamiento. 
    user_file: Excel que subió el usuario.
    process_id: para poder enviar mensajes SSE en tiempo real.
    """
    # user_file -> el Excel que subió el usuario con 'Operation Activities'
    sse_manager.send_message(process_id, "Leyendo archivo del usuario...")
    await asyncio.sleep(1)

    df_actividades = pd.read_excel(user_file)

    # Procesar el archivo de actividades
    sse_manager.send_message(process_id, "Detectando C0, C1, C2, C3...")
    await asyncio.sleep(1)

    ordenes_procesadas = {}
    for _, row in df_actividades.iterrows():
        # Ejemplo: 'Effectivity' = "modelo,00001"
        modelo, unidad = row['Effectivity'].split(',')
        unidad = unidad.lstrip('0')  # Quitar ceros a la izquierda
        orden = (modelo, unidad)

        if orden not in ordenes_procesadas:
            ordenes_procesadas[orden] = {'C0': [], 'C1': [], 'C2': [], 'C3': []}

        for c in ['C0', 'C1', 'C2', 'C3']:
            if f'({c}' in row['Operation Activity']:
                orden_sin_parentesis = row['Order'].replace('(', '').replace(')', '')
                if orden_sin_parentesis not in ordenes_procesadas[orden][c]:
                    ordenes_procesadas[orden][c].append(orden_sin_parentesis)

    # Obtener avisos de calidad desde un directorio local del servidor
    # archivo_avisos = encontrar_archivo_mas_reciente()
    # Definir la ruta al archivo AVISOS_CALIDAD.xlsx dentro del backend
    # Hardcodeada para simplificar el ejemplo
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Obtiene /backend/app
    TMP_DIR = os.path.join(BASE_DIR, "..", "tmp")  # Sube a /backend y entra en /tmp
    archivo_avisos = os.path.join(TMP_DIR, "AVISOS_CALIDAD.xlsx")

    # Asegurar que la ruta se resuelve correctamente en Docker/Linux
    archivo_avisos = os.path.abspath(archivo_avisos)

    avisos_calidad = extraer_avisos_de_calidad(archivo_avisos)

    # Crear un nuevo Excel
    sse_manager.send_message(process_id, "Creando archivo resultante...")
    await asyncio.sleep(1)
    wb = Workbook()
    ws = wb.active

    # Cabecera con columnas extra
    ws.append([
        'MODELO', 'UNIDAD',
        'ORDENES C0', 'CANT. C0s',
        'AVISO CALIDAD C1', 'CANT. AV. C1', 'ORDENES C1', 'CANT. C1s',
        'AVISO CALIDAD C2', 'CANT. AV. C2', 'ORDENES C2', 'CANT. C2s',
        'AVISO CALIDAD C3', 'CANT. AV. C3', 'ORDENES C3', 'CANT. C3s'
    ])

    for (modelo, unidad), codigos in ordenes_procesadas.items():
        fila = [modelo, unidad]
        # C0
        ordenes_c0 = ', '.join(codigos['C0'])
        cantidad_c0s = len(codigos['C0'])
        fila.extend([ordenes_c0, cantidad_c0s])

        # C1, C2, C3
        for c in ['C1', 'C2', 'C3']:
            avisos = ', '.join(avisos_calidad[c].get(modelo, []))
            cantidad_avisos = len(avisos_calidad[c].get(modelo, []))
            ordenes_c = ', '.join(codigos[c])
            cantidad_cs = len(codigos[c])
            fila.extend([avisos, cantidad_avisos, ordenes_c, cantidad_cs])

        ws.append(fila)

    # Ordenar, formatear, etc.
    sse_manager.send_message(process_id, "Ordenando registros y aplicando formato...")
    await asyncio.sleep(1)
    
    ordenar_registros(ws)
    aplicar_formato(ws)
    aplicar_formato_condicional(ws)

    # Guardar el archivo resultante
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo_resultante = f"Extraciclos_Pendientes_{timestamp}.xlsx"
    ruta_resultado = os.path.join("/tmp", nombre_archivo_resultante)  # o la carpeta que desees en el servidor
    wb.save(ruta_resultado)

    return ruta_resultado
