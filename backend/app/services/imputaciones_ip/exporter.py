# PATH: manual-imputaciones-ip/etl/exporter.py

from datetime import datetime
import os

# Fase 3: Generación del Archivo de Salida

def generar_csv_salida(horas_proyecto, output_dir):
    # Iterar sobre cada valor único en la columna 'Cost'
    for cost_value in horas_proyecto['Cost'].unique():
        # Filtrar el DataFrame por el valor actual de 'Cost'
        df_filtrado = horas_proyecto[horas_proyecto['Cost'] == cost_value]
        
        # Crear el nombre del archivo basado en el valor de 'Cost' y el timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_path = f"{output_dir}/SAP_EXPORT_{cost_value}_{timestamp}.csv"
        
        # Guardar en formato CSV con ; como separador
        df_filtrado.to_csv(output_path, sep=';', index=False)
        print(f"Archivo exportado a {output_path}")


def generar_cuadre_xlsx(cuadre_horas, output_dir):
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_path = os.path.join(output_dir, f"cuadre_horas_{timestamp}.xlsx")
    
    # Guardar el DataFrame en un archivo Excel
    cuadre_horas.to_excel(output_path, index=False)
    print(f"Archivo de cuadre de horas exportado a {output_path}")
