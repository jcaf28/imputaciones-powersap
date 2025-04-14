import React from "react";
import { Box, Typography, Button, CircularProgress } from "@mui/material";
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
    handleCancel,
    downloadCSV,
    rowCount,
    showingRows,
    toggleShowRows
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
          Descargar CSV Generado
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


