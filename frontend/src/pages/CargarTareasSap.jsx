// PATH: frontend/src/pages/CargarTareasSap.jsx

import { useState } from "react";
import { Button, Typography } from "@mui/material";
import FileUploadChecker from "../components/FileUploadChecker";
import useCargarTareasSAP from "../hooks/useCargarTareasSAP";

export const meta = {
  label: "Cargar tareas SAP", // para tu sidebar
  priority: 1
};

export default function CargarTareasSAP() {
  const {
    file,
    validated,
    status,
    message,
    error,
    isUploading,
    setFileHandler,
    validateFileHandler,
    handleStartProcess,
    handleCancel
  } = useCargarTareasSAP();

  return (
    <div style={{ margin: 20 }}>
      <Typography variant="h4" gutterBottom>
        Cargar Tareas SAP
      </Typography>

      {/* Puede usar tu componente FileUploadChecker o algo similar */}
      <FileUploadChecker
        label="Archivo SAP (un solo .xlsx)"
        index={0}
        file={file}
        validated={validated}
        onFileChange={(_index, uploadedFile) => setFileHandler(uploadedFile)}
        onValidate={validateFileHandler}
      />

      {/* Botones para iniciar y cancelar */}
      <div style={{ marginTop: 10 }}>
        <Button
          variant="contained"
          onClick={handleStartProcess}
          disabled={!validated || isUploading || status === "in-progress"}
        >
          Iniciar proceso
        </Button>

        <Button
          variant="outlined"
          onClick={handleCancel}
          disabled={!file || status !== "in-progress"}
          style={{ marginLeft: 8 }}
        >
          Cancelar
        </Button>
      </div>

      {/* Estado */}
      <div style={{ marginTop: 10 }}>
        <Typography variant="body1">
          <strong>Status:</strong> {status}
        </Typography>
        <Typography variant="body1">
          <strong>Mensaje:</strong> {message}
        </Typography>
        {error && (
          <Typography variant="body1" color="error">
            <strong>Error:</strong> {error}
          </Typography>
        )}
      </div>
    </div>
  );
}
