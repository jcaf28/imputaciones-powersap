// PATH: frontend/src/pages/GererarImputacionesSap.jsx

import React from "react";
import { Box, Typography, Button, CircularProgress, Alert } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";

import useGenerarImputacionesSap from "../hooks/useGenerarImputacionesSap";
import ProcessLogger from "../components/ProcessLogger";

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
    handleForceStart,
    handleDismissWarning,
    handleCancel,
    downloadCSV,
    rowCount,
    showingRows,
    toggleShowRows,
    pendingWarning
  } = useGenerarImputacionesSap();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Generar Imputaciones SAP
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body1" sx={{ mb: 1 }}>
          {rowCount !== null
            ? `Registros pendientes encontrados: ${rowCount}`
            : "Contando registros..."}
        </Typography>
        <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="contained"
            onClick={handleStartProcess}
            disabled={loading || status === "in-progress"}
          >
            Generar Imputaciones SAP
          </Button>

          <Button
            variant="outlined"
            onClick={toggleShowRows}
            disabled={loading || status === "in-progress"}
          >
            {showingRows ? "Refrescar" : "Ver registros"}
          </Button>

          {status === "in-progress" && (
            <Button variant="outlined" color="error" onClick={handleCancel}>
              Cancelar
            </Button>
          )}
        </Box>
      </Box>

      {pendingWarning && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {pendingWarning.message}
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button size="small" variant="contained" color="warning" onClick={handleForceStart}>
              Continuar igualmente
            </Button>
            <Button size="small" variant="outlined" onClick={handleDismissWarning}>
              Cancelar
            </Button>
          </Box>
        </Alert>
      )}

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

      {(status === "in-progress" || status === "completed") && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">Progreso:</Typography>
          <ProcessLogger logs={logs} title="Log de Generación SAP" />
        </Box>
      )}

      {status === "completed" && (
        <Button variant="contained" onClick={downloadCSV}>
          Descargar ZIP (CSV + XLSX)
        </Button>
      )}

      {showingRows && (
        <Box sx={{ height: 500, mt: 2 }}>
          <DataGrid
            rows={rows}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10, 25, 50]}
            loading={loading && status !== "in-progress"}
            disableSelectionOnClick
          />
        </Box>
      )}
    </Box>
  );
}


