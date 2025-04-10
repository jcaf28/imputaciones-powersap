// PATH: frontend/src/components/FileUploadChecker.jsx

import { Box, Button, TextField, Typography } from "@mui/material";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { CircularProgress } from "@mui/material";
import { useEffect } from "react";

export default function FileUploadChecker({
  label,
  index,
  file,
  validated,
  onFileChange,
  onValidate,
}) {
  useEffect(() => {
    if (file) {
      onValidate(index);
    }
  }, [file]); // <- solo cuando el archivo cambia
  return (
    <Box sx={{ mb: 3 }}>
      {/* Etiqueta para indicar qué archivo es */}
      <Typography variant="subtitle1">{label}</Typography>

      {/* Input del archivo */}
      <TextField
        type="file"
        slotProps={{ input: { accept: ".xlsx" } }}
        onChange={(e) => {
          const uploadedFile = e.target.files[0];
          onFileChange(index, uploadedFile);
        }}
      />

      {/* Indicador visual si está validado o no */}
      {validated ? (
        <CheckCircleOutlineIcon
          sx={{ color: "green", ml: 1, verticalAlign: "middle" }}
        />
      ) : file ? (
        // Si hay un archivo pero aún no está validado
        <CircularProgress
          sx={{ color: "gray", ml: 1, verticalAlign: "middle" }}
        />
      ) : null}
    </Box>
  );
}
