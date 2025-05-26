// PATH: frontend/src/components/DeleteConfirmDialog.jsx

import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  useTheme,
} from "@mui/material";
import { Delete, Cancel, Warning } from "@mui/icons-material";

export default function DeleteConfirmDialog({
  open,
  onClose,
  onConfirm,
  proyecto = null,
  loading = false,
}) {
  const theme = useTheme();

  if (!proyecto) return null;

  const hasImputaciones = proyecto.imputaciones_count > 0;

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: theme.palette.background.paper,
          borderRadius: theme.shape.borderRadius,
        }
      }}
    >
      <DialogTitle
        sx={{
          backgroundColor: theme.palette.error.main,
          color: theme.palette.error.contrastText,
          fontWeight: theme.typography.h5.fontWeight,
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        <Warning />
        Confirmar Eliminación
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="body1">
            ¿Estás seguro de que quieres eliminar el siguiente proyecto?
          </Typography>

          <Box
            sx={{
              p: 2,
              backgroundColor: theme.palette.background.default,
              borderRadius: theme.shape.borderRadius,
              border: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography variant="subtitle2" color="primary">
              Proyecto BAAN:
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
              {proyecto.ProyectoBaan}
            </Typography>
            
            <Typography variant="subtitle2" color="primary">
              Proyecto SAP:
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
              {proyecto.ProyectoSap || "(No especificado)"}
            </Typography>
            
            <Typography variant="subtitle2" color="primary">
              Imputaciones asociadas:
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              {proyecto.imputaciones_count}
            </Typography>
          </Box>

          {hasImputaciones ? (
            <Alert severity="error">
              <Typography variant="body2">
                <strong>No se puede eliminar este proyecto</strong> porque tiene{" "}
                {proyecto.imputaciones_count} imputación(es) asociada(s).
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Para eliminar este proyecto, primero debes eliminar o reasignar 
                todas las imputaciones asociadas.
              </Typography>
            </Alert>
          ) : (
            <Alert severity="warning">
              <Typography variant="body2">
                <strong>Esta acción no se puede deshacer.</strong> Una vez eliminado, 
                el proyecto no podrá ser recuperado.
              </Typography>
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          onClick={onClose}
          disabled={loading}
          startIcon={<Cancel />}
          sx={{
            color: theme.palette.text.secondary,
            "&:hover": {
              backgroundColor: theme.palette.action.hover,
            },
          }}
        >
          Cancelar
        </Button>
        
        <Button
          onClick={onConfirm}
          variant="contained"
          disabled={loading || hasImputaciones}
          startIcon={<Delete />}
          sx={{
            backgroundColor: theme.palette.error.main,
            color: theme.palette.error.contrastText,
            "&:hover": {
              backgroundColor: theme.palette.error.dark,
            },
            "&:disabled": {
              backgroundColor: theme.palette.action.disabledBackground,
              color: theme.palette.action.disabled,
            },
          }}
        >
          {loading ? "Eliminando..." : "Eliminar Proyecto"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}