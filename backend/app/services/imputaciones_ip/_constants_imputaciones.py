# PATH: backend/app/services/imputaciones_ip/_constants_imputaciones.py

COLUMNAS_MINIMAS = {
    "descarga_imputaciones": [
        "Id.", "Usuario", "Fecha", "Clave Obra", "CodObra", "OBRA", "Proceso",
        "IdTarea", "TAREA", "Descripción", "Plano", "Horas", "Euros", "VALIDADA",
        "TIPO", "OBRA_1", "QTY_1", "OBRA_2", "QTY_2", "Nº Mod. OT"
    ],
    "listado_usuarios": [
        "IdUsuario", "Usuario", "WBS", "Cost", "Cost_2"
    ],
    "wbs_por_clave": [
        "PROYECTO BAAN", "PROYECTO SAP", "WBS PROCESOS (FMOP3)",
        "WBS UTILLAJES (FU300)", "PSA"
    ],
    "fichajes_sap": [
        "Centro", "Sociedad", "Intervalo de fechas", "Número de empleado", "Nombre del empleado",
        "Supervisor", "Nombre del equipo", "ClockedHRS", "ManufacturingHrs", "OverCostHrs",
        "IndirectHrs", "ProjectHrs", "MaintenanceHrs", "TotConfirmHrs", "TotalApprovedHours",
        "DifferenceClockedConfirmed", "DifferenceConfirmedApproved"
    ]
}
