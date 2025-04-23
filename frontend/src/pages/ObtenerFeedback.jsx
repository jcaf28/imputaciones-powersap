// PATH: frontend/src/pages/ObtenerFeedback.jsx

import {
  Box,
  Button,
  CircularProgress,
  Typography,
} from "@mui/material";
import FileUploadChecker from "../components/FileUploadChecker";
import ProcessLogger from "../components/ProcessLogger";
import useObtenerFeedback from "../hooks/useObtenerFeedback";

export const meta = {
  label: "Obtener Feedback",
  priority: 5,
};

export default function ObtenerFeedback() {
  const {
    file,
    validated,
    status,
    error,
    isUploading,
    logs,
    downloadUrl,     // 👈 nuevo
    setFile,
    validateFile,
    startProcess,
    cancelProcess,
  } = useObtenerFeedback();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Obtener Feedback
      </Typography>

      <FileUploadChecker
        label="Archivo de feedback (.xlsx)"
        index={0}
        file={file}
        validated={validated}
        onFileChange={(_i, newFile) => setFile(newFile)}
        onValidate={validateFile}
      />

      {/* Botones de control */}
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          disabled={!validated || isUploading || status === "in-progress"}
          onClick={startProcess}
          sx={{ mr: 1 }}
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

      {/* Botón de descarga cuando termina */}
      {status === "completed" && downloadUrl && (
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            color="success"
            onClick={() => window.open(downloadUrl, "_blank")}
          >
            Descargar archivo procesado
          </Button>
        </Box>
      )}

      {/* Estado + Logger */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="body1" sx={{ mb: 1 }}>
          <strong>Status:</strong> {status}
        </Typography>

        {status === "in-progress" && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              mb: 2,
            }}
          >
            <CircularProgress size={20} />
            <Typography variant="body2">Procesando...</Typography>
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
