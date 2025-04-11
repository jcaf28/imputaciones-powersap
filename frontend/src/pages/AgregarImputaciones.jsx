// PATH: frontend/src/pages/AgregarImputaciones.jsx

import { Button, Typography, Box, CircularProgress } from "@mui/material";
import FileUploadChecker from "../components/FileUploadChecker";
import ProcessLogger from "../components/ProcessLogger"; 
import useAgregarImputaciones from "../hooks/useAgregarImputaciones";

export const meta = {
  label: "Agregar Imputaciones", // nombre para el sidebar
  priority: 2
};

export default function AgregarImputaciones() {
  const {
    file,
    validated,
    status,
    error,
    logs,
    isUploading,
    setFileHandler,
    validateFileHandler,
    handleStartProcess,
    handleCancel
  } = useAgregarImputaciones();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Agregar Imputaciones
      </Typography>

      <FileUploadChecker
        label="Archivo Imputaciones (.xlsx)"
        index={0}
        file={file}
        validated={validated}
        onFileChange={(_index, uploadedFile) => setFileHandler(uploadedFile)}
        onValidate={validateFileHandler}
      />

      {/* Botones para iniciar y cancelar */}
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          onClick={handleStartProcess}
          disabled={!validated || isUploading || status === "in-progress"}
          sx={{ mr: 1 }}
        >
          Iniciar proceso
        </Button>

        <Button
          variant="outlined"
          onClick={handleCancel}
          disabled={!file || status !== "in-progress"}
        >
          Cancelar
        </Button>
      </Box>

      {/* Estado + Logger */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="body1" sx={{ mb: 1 }}>
          <strong>Status:</strong> {status}
        </Typography>

        {status === "in-progress" && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: 1,
              mb: 2
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
