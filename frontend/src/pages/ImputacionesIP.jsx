// PATH: frontend/src/pages/ImputacionesIP.jsx

import { Box, Typography } from "@mui/material";
import useImputacionesIP from "../hooks/useImputacionesIP";
import ImputacionesIPForm from "../components/ImputacionesIPForm";
import ImputacionesIPStatus from "../components/ImputacionesIPStatus";

export default function ImputacionesIP() {
  const {
    files,
    validations,
    setFile,
    validateFile,
    canGenerate,
    isUploading,
    status,
    message,
    error,
    handleGenerate,
    handleCancel,
    handleDownload,
  } = useImputacionesIP();

  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography variant="h5" sx={{ mb:2, mt: 4, fontWeight: "bold", textTransform: "uppercase", letterSpacing: 1 }}>
        Generador de Imputaciones SAP
      </Typography>

      <Typography variant="body1" sx={{ mt: 1, maxWidth: 600, mx: "auto", color: "text.secondary" }}>
        Esta herramienta permite validar los archivos de cierre del departamento IP y generar automáticamente los ficheros de imputación compatibles con SAP. Sigue los pasos a continuación para cargar los datos y obtener los archivos de imputaciones con el formato de SAP
      </Typography>

      <ImputacionesIPForm
        files={files}
        validations={validations}
        setFile={setFile}
        validateFile={validateFile}
        canGenerate={canGenerate}
        onGenerate={handleGenerate}
        isUploading={isUploading}
      />

      <ImputacionesIPStatus
        status={status}
        message={message}
        error={error}
        isUploading={isUploading}
        onCancel={handleCancel}
        onDownload={handleDownload}
      />
    </Box>
  );
}
