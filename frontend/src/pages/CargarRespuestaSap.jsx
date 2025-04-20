// PATH: frontend/src/pages/CargarRespuestaSap.jsx

import { Button, Typography, Box, CircularProgress } from "@mui/material";
import FileUploadChecker from "../components/FileUploadChecker";
import ProcessLogger from "../components/ProcessLogger";
import useCargarRespuestaSap from "../hooks/useCargarRespuestaSap";

export const meta = { label: "Cargar Respuesta SAP", priority: 1 };

export default function CargarRespuestaSap() {
  const {
    file, validated, status, error, isUploading, logs,
    setFile, validateFileHandler, startProcess, cancelProcess
  } = useCargarRespuestaSap();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Cargar Respuesta SAP
      </Typography>

      <FileUploadChecker
        label="Respuesta SAP (.xlsx)"
        index={0}
        file={file}
        validated={validated}
        onFileChange={(_, f) => setFile(f)}
        onValidate={validateFileHandler}
      />

      {/* Botones */}
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          sx={{ mr: 1 }}
          disabled={!validated || isUploading || status === "in-progress"}
          onClick={startProcess}
        >
          Iniciar proceso
        </Button>
        <Button
          variant="outlined"
          disabled={!file || status !== "in-progress"}
          onClick={cancelProcess}
        >
          Cancelar
        </Button>
      </Box>

      {/* Estado + logger */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="body1"><strong>Status:</strong> {status}</Typography>

        {status === "in-progress" && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, my: 2 }}>
            <CircularProgress size={20} />
            <Typography variant="body2">Procesando…</Typography>
          </Box>
        )}

        <ProcessLogger logs={logs} title="Log del proceso" />

        {error && (
          <Typography variant="body1" color="error" sx={{ mt: 2 }}>
            <strong>Error:</strong> {error}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
