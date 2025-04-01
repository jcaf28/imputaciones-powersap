// PATH: frontend/src/components/ImputacionesIPStatus.jsx

import { Box, Typography, CircularProgress, Button } from "@mui/material";

export default function ImputacionesIPStatus({
  status,
  message,
  error,
  isUploading,
  onCancel,
  onDownload,
}) {
  return (
    <Box sx={{ mt: 4 }}>
      {isUploading && (
        <Typography variant="body1" sx={{ mt: 2 }}>
          Subiendo archivos al servidor...
        </Typography>
      )}

      {status === "in-progress" && (
        <>
          <CircularProgress size="2rem" />
          <Typography variant="body1" sx={{ mt: 2 }}>
            {message}
          </Typography>
          <Button variant="outlined" color="warning" onClick={onCancel} sx={{ ml: 2 }}>
            Cancelar
          </Button>
        </>
      )}

      {status === "completed" && (
        <>
          <Typography sx={{ color: "green" }}>
            {message || "¡Proceso completado!"}
          </Typography>
          <Button variant="contained" sx={{ mt: 2 }} onClick={onDownload}>
            Descargar resultado
          </Button>
        </>
      )}

      {status === "cancelled" && (
        <Typography sx={{ color: "orange" }}>
          {message || "Proceso cancelado"}
        </Typography>
      )}

      {status === "error" && (
        <Typography sx={{ color: "red" }}>
          Error: {error}
        </Typography>
      )}
    </Box>
  );
}
