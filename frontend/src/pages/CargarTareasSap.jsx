// PATH: frontend/src/pages/CargarTareasSap.jsx

import { Button, Typography, Box } from "@mui/material";
import FileUploadChecker from "../components/FileUploadChecker";
import useCargarTareasSap from "../hooks/useCargarTareasSap";
import ProcessLogger from "../components/ProcessLogger"; // <-- nuevo

export const meta = {
  label: "Cargar tareas SAP",
  priority: 1
};

export default function CargarTareasSAP() {
  const {
    file,
    validated,
    status,
    error,
    isUploading,
    logs,
    setFileHandler,
    validateFileHandler,
    handleStartProcess,
    handleCancel
  } = useCargarTareasSap();

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Cargar Tareas SAP
      </Typography>

      <FileUploadChecker
        label="Archivo SAP (un solo .xlsx)"
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

      {/* Estado y logger */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="body1" sx={{ mb: 1 }}>
          <strong>Status:</strong> {status}
        </Typography>

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
