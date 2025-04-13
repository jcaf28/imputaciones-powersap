// PATH: frontend/src/pages/GererarImputacionesSap.jsx

import React from "react";
import { Box, Typography, Button, CircularProgress } from "@mui/material";
import { DataGrid, GridToolbarQuickFilter } from "@mui/x-data-grid";

import useGenerarImputacionesSap from "../hooks/useGenerarImputacionesSap";
import ProcessLogger from "../components/ProcessLogger"; // Reutiliza tu componente

export const meta = {
  label: "Generar Imputaciones SAP",
  priority: 3
};

export default function GenerarImputacionesSap() {
  const {
    rows,
    columns,
    loading,
    error,
    status,
    logs,
    processId,
    handleStartProcess,
    handleCancel,
    refreshData,
    downloadCSV
  } = useGenerarImputacionesSap();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Generar Imputaciones SAP
      </Typography>

      <Box sx={{ mb: 2, display: "flex", gap: 2 }}>
        {/* Botón que inicia la generación con SSE */}
        <Button
          variant="contained"
          onClick={handleStartProcess}
          disabled={loading || status === "in-progress"}
        >
          Generar Imputaciones SAP
        </Button>

        {/* Botón para refrescar la tabla de pendientes */}
        <Button
          variant="outlined"
          onClick={refreshData}
          disabled={loading || status === "in-progress"}
        >
          Refrescar datos
        </Button>

        {/* Botón para cancelar SSE */}
        {status === "in-progress" && (
          <Button variant="outlined" color="error" onClick={handleCancel}>
            Cancelar
          </Button>
        )}
      </Box>

      {loading && status !== "in-progress" && (
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <CircularProgress size={20} />
          <Typography variant="body1" sx={{ ml: 1 }}>
            Cargando...
          </Typography>
        </Box>
      )}

      {error && (
        <Typography variant="body1" color="error" sx={{ mb: 2 }}>
          Error: {error}
        </Typography>
      )}

      {/* Logs SSE si está in-progress o completado */}
      {(status === "in-progress" || status === "completed") && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Progreso:</Typography>
          <ProcessLogger logs={logs} title="Log de Generación SAP" />
        </Box>
      )}

      {/* Si completado, permitir descarga CSV */}
      {status === "completed" && (
        <Button variant="contained" onClick={downloadCSV}>
          Descargar CSV Generado
        </Button>
      )}

      <Box sx={{ height: 500, mt: 2 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          pageSize={10}
          rowsPerPageOptions={[10, 25, 50]}
          loading={loading && status !== "in-progress"}
          disableSelectionOnClick
          components={{
            Toolbar: QuickSearchToolbar
          }}
        />
      </Box>
    </Box>
  );
}

// Barra de búsqueda rápida (filtra en todas las columnas)
function QuickSearchToolbar() {
  return (
    <Box
      sx={{
        p: 1,
        pb: 0,
        display: "flex",
        justifyContent: "flex-end"
      }}
    >
      <GridToolbarQuickFilter />
    </Box>
  );
}
