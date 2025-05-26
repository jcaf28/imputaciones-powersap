// PATH: frontend/src/pages/Proyectos.jsx

import {
  Box,
  Typography,
  Button,
  TextField,
  Alert,
  IconButton,
  Tooltip,
  useTheme,
  Paper,
  Chip,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import {
  Add,
  Edit,
  Delete,
  Search,
  Refresh,
  Assignment,
} from "@mui/icons-material";

import useProyectos from "../hooks/useProyectos";
import ProyectoForm from "../components/ProyectoForm";
import DeleteConfirmDialog from "../components/DeleteConfirmDialog";

export const meta = {
  label: "Proyectos",
  priority: 6,
};

export default function Proyectos() {
  const theme = useTheme();
  const {
    // Estado
    proyectos,
    loading,
    error,
    searchTerm,
    selectedProyecto,
    columns,
    
    // Estados de modals
    formModalOpen,
    deleteModalOpen,
    formMode,
    
    // Setters
    setSearchTerm,
    setError,
    
    // Acciones
    handleCreate,
    handleUpdate,
    handleDelete,
    loadProyectos,
    
    // Modal controllers
    openCreateModal,
    openEditModal,
    openDeleteModal,
    closeFormModal,
    closeDeleteModal,
  } = useProyectos();

  // Preparar filas para el DataGrid con botones de acción
  const rowsWithActions = proyectos.map((proyecto) => ({
    ...proyecto,
    id: proyecto.ProyectoBaan, // DataGrid necesita un campo 'id'
    actions: (
      <Box sx={{ display: "flex", gap: 0.5 }}>
        <Tooltip title="Editar proyecto">
          <IconButton
            size="small"
            onClick={() => openEditModal(proyecto)}
            sx={{
              color: theme.palette.primary.main,
              "&:hover": {
                backgroundColor: theme.palette.primary.main + "20",
              },
            }}
          >
            <Edit fontSize="small" />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Eliminar proyecto">
          <IconButton
            size="small"
            onClick={() => openDeleteModal(proyecto)}
            sx={{
              color: theme.palette.error.main,
              "&:hover": {
                backgroundColor: theme.palette.error.main + "20",
              },
            }}
          >
            <Delete fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    ),
  }));

  return (
    <Box sx={{ p: 2 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography
          variant="h4"
          sx={{
            color: theme.palette.primary.main,
            fontWeight: theme.typography.h4.fontWeight,
          }}
        >
          Gestión de Proyectos
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={openCreateModal}
          sx={{
            backgroundColor: theme.palette.primary.main,
            "&:hover": {
              backgroundColor: theme.palette.primary.dark,
            },
            fontWeight: theme.typography.button.fontWeight,
          }}
        >
          Nuevo Proyecto
        </Button>
      </Box>

      {/* Barra de herramientas */}
      <Paper
        sx={{
          p: 2,
          mb: 2,
          backgroundColor: theme.palette.background.paper,
          borderRadius: theme.shape.borderRadius,
        }}
      >
        <Box
          sx={{
            display: "flex",
            gap: 2,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: 1, minWidth: 300 }}>
            <Search sx={{ color: theme.palette.text.secondary }} />
            <TextField
              placeholder="Buscar por Proyecto BAAN o SAP..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              variant="outlined"
              size="small"
              fullWidth
              sx={{
                "& .MuiOutlinedInput-root": {
                  backgroundColor: theme.palette.background.default,
                },
              }}
            />
          </Box>
          
          <Tooltip title="Actualizar lista">
            <IconButton
              onClick={() => loadProyectos(searchTerm)}
              disabled={loading}
              sx={{
                color: theme.palette.primary.main,
                "&:hover": {
                  backgroundColor: theme.palette.primary.main + "20",
                },
              }}
            >
              <Refresh />
            </IconButton>
          </Tooltip>

          <Chip
            icon={<Assignment />}
            label={`${proyectos.length} proyecto(s)`}
            variant="outlined"
            sx={{
              borderColor: theme.palette.primary.main,
              color: theme.palette.primary.main,
            }}
          />
        </Box>
      </Paper>

      {/* Alert de error */}
      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      )}

      {/* DataGrid */}
      <Paper
        sx={{
          height: 600,
          backgroundColor: theme.palette.background.paper,
          borderRadius: theme.shape.borderRadius,
          "& .MuiDataGrid-root": {
            border: "none",
            "& .MuiDataGrid-cell": {
              borderBottom: `1px solid ${theme.palette.divider}`,
            },
            "& .MuiDataGrid-columnHeaders": {
              backgroundColor: theme.palette.primary.main,
              color: theme.palette.primary.contrastText,
              fontWeight: theme.typography.h6.fontWeight,
              "& .MuiDataGrid-columnHeader": {
                "&:focus": {
                  outline: "none",
                },
              },
            },
            "& .MuiDataGrid-row": {
              "&:hover": {
                backgroundColor: theme.palette.action.hover,
              },
              "&:nth-of-type(even)": {
                backgroundColor: theme.palette.background.default,
              },
            },
            "& .MuiDataGrid-footerContainer": {
              borderTop: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.default,
            },
          },
        }}
      >
        <DataGrid
          rows={rowsWithActions}
          columns={columns}
          pageSize={25}
          rowsPerPageOptions={[10, 25, 50, 100]}
          loading={loading}
          disableSelectionOnClick
          autoHeight={false}
          getRowHeight={() => 52}
          localeText={{
            noRowsLabel: "No se encontraron proyectos",
            toolbarFilters: "Filtros",
            toolbarFiltersLabel: "Mostrar filtros",
            toolbarDensity: "Densidad",
            toolbarDensityLabel: "Densidad",
            toolbarDensityCompact: "Compacta",
            toolbarDensityStandard: "Estándar",
            toolbarDensityComfortable: "Cómoda",
            toolbarColumns: "Columnas",
            toolbarColumnsLabel: "Seleccionar columnas",
            footerRowSelected: (count) =>
              count !== 1
                ? `${count.toLocaleString()} filas seleccionadas`
                : `${count.toLocaleString()} fila seleccionada`,
          }}
          sx={{
            "& .MuiDataGrid-cell": {
              fontSize: theme.typography.body2.fontSize,
            },
          }}
        />
      </Paper>

      {/* Modal de formulario */}
      <ProyectoForm
        open={formModalOpen}
        onClose={closeFormModal}
        onSubmit={formMode === "create" ? handleCreate : handleUpdate}
        proyecto={selectedProyecto}
        mode={formMode}
        loading={loading}
      />

      {/* Modal de confirmación de eliminación */}
      <DeleteConfirmDialog
        open={deleteModalOpen}
        onClose={closeDeleteModal}
        onConfirm={handleDelete}
        proyecto={selectedProyecto}
        loading={loading}
      />
    </Box>
  );
}