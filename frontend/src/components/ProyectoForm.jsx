// PATH: frontend/src/components/ProyectoForm.jsx

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  useTheme,
  Typography,
} from "@mui/material";
import { Save, Cancel } from "@mui/icons-material";

export default function ProyectoForm({
  open,
  onClose,
  onSubmit,
  proyecto = null,
  mode = "create", // "create" | "edit"
  loading = false,
}) {
  const theme = useTheme();
  const [formData, setFormData] = useState({
    ProyectoBaan: "",
    ProyectoSap: "",
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");

  const isEditMode = mode === "edit";
  const title = isEditMode ? "Editar Proyecto" : "Crear Nuevo Proyecto";

  // Resetear form cuando se abre/cierra o cambia el proyecto
  useEffect(() => {
    if (open) {
      if (isEditMode && proyecto) {
        setFormData({
          ProyectoBaan: proyecto.ProyectoBaan || "",
          ProyectoSap: proyecto.ProyectoSap || "",
        });
      } else {
        setFormData({
          ProyectoBaan: "",
          ProyectoSap: "",
        });
      }
      setErrors({});
      setSubmitError("");
    }
  }, [open, proyecto, isEditMode]);

  // Validación del formulario
  const validateForm = () => {
    const newErrors = {};

    if (!formData.ProyectoBaan.trim()) {
      newErrors.ProyectoBaan = "El Proyecto BAAN es obligatorio";
    } else if (formData.ProyectoBaan.length > 255) {
      newErrors.ProyectoBaan = "El Proyecto BAAN no puede tener más de 255 caracteres";
    }

    if (formData.ProyectoSap && formData.ProyectoSap.length > 255) {
      newErrors.ProyectoSap = "El Proyecto SAP no puede tener más de 255 caracteres";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Manejar cambios en inputs
  const handleInputChange = (field) => (event) => {
    const value = event.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Limpiar error del campo específico
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: "",
      }));
    }
  };

  // Manejar submit
  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitError("");

    if (!validateForm()) {
      return;
    }

    try {
      const dataToSubmit = isEditMode
        ? { ProyectoSap: formData.ProyectoSap } // En edición solo enviamos ProyectoSap
        : formData; // En creación enviamos todo

      const result = await onSubmit(dataToSubmit);
      
      if (!result.success) {
        setSubmitError(result.error || "Error al procesar la solicitud");
      }
    } catch (error) {
      setSubmitError("Error inesperado al procesar la solicitud");
    }
  };

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
          backgroundColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          fontWeight: theme.typography.h5.fontWeight,
        }}
      >
        {title}
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent sx={{ pt: 3 }}>
          {submitError && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              onClose={() => setSubmitError("")}
            >
              {submitError}
            </Alert>
          )}

          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Proyecto BAAN"
              value={formData.ProyectoBaan}
              onChange={handleInputChange("ProyectoBaan")}
              error={!!errors.ProyectoBaan}
              helperText={errors.ProyectoBaan || (isEditMode ? "No se puede modificar (clave primaria)" : "")}
              disabled={isEditMode || loading}
              required={!isEditMode}
              fullWidth
              variant="outlined"
              sx={{
                "& .MuiOutlinedInput-root": {
                  backgroundColor: isEditMode 
                    ? theme.palette.action.disabledBackground 
                    : theme.palette.background.default,
                },
              }}
            />

            <TextField
              label="Proyecto SAP"
              value={formData.ProyectoSap}
              onChange={handleInputChange("ProyectoSap")}
              error={!!errors.ProyectoSap}
              helperText={errors.ProyectoSap || "Código del proyecto en SAP (opcional)"}
              disabled={loading}
              fullWidth
              variant="outlined"
              sx={{
                "& .MuiOutlinedInput-root": {
                  backgroundColor: theme.palette.background.default,
                },
              }}
            />

            {isEditMode && proyecto?.imputaciones_count > 0 && (
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="body2">
                  Este proyecto tiene {proyecto.imputaciones_count} imputación(es) asociada(s).
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
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={<Save />}
            sx={{
              backgroundColor: theme.palette.primary.main,
              "&:hover": {
                backgroundColor: theme.palette.primary.dark,
              },
            }}
          >
            {loading ? "Guardando..." : isEditMode ? "Actualizar" : "Crear"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}