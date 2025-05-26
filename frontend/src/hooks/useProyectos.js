// PATH: frontend/src/hooks/useProyectos.js

import { useState, useEffect, useCallback } from "react";
import {
  fetchProyectos,
  createProyecto,
  updateProyecto,
  deleteProyecto,
} from "../services/proyectosService";

export default function useProyectos() {
  // Estado principal
  const [proyectos, setProyectos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Estados para UI
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProyecto, setSelectedProyecto] = useState(null);
  
  // Estados para modals
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [formMode, setFormMode] = useState("create"); // "create" | "edit"

  // Columnas para el DataGrid (usando el tema de manera paramétrica)
  const columns = [
    {
      field: "ProyectoBaan",
      headerName: "Proyecto BAAN",
      width: 200,
      editable: false,
    },
    {
      field: "ProyectoSap",
      headerName: "Proyecto SAP",
      width: 200,
      editable: false,
    },
    {
      field: "imputaciones_count",
      headerName: "Imputaciones",
      width: 120,
      type: "number",
      editable: false,
    },
    {
      field: "actions",
      headerName: "Acciones",
      width: 200,
      sortable: false,
      renderCell: (params) => params.value, // Se renderizará desde el componente
    },
  ];

  // Cargar proyectos
  const loadProyectos = useCallback(async (search = "") => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProyectos({ search });
      setProyectos(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al cargar proyectos");
    } finally {
      setLoading(false);
    }
  }, []);

  // Efecto inicial
  useEffect(() => {
    loadProyectos();
  }, [loadProyectos]);

  // Efecto para búsqueda con debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadProyectos(searchTerm);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchTerm, loadProyectos]);

  // Crear proyecto
  const handleCreate = async (proyectoData) => {
    try {
      setLoading(true);
      await createProyecto(proyectoData);
      await loadProyectos(searchTerm);
      setFormModalOpen(false);
      return { success: true };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || "Error al crear proyecto";
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Actualizar proyecto
  const handleUpdate = async (proyectoData) => {
    if (!selectedProyecto) return { success: false, error: "No hay proyecto seleccionado" };
    
    try {
      setLoading(true);
      await updateProyecto(selectedProyecto.ProyectoBaan, proyectoData);
      await loadProyectos(searchTerm);
      setFormModalOpen(false);
      setSelectedProyecto(null);
      return { success: true };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || "Error al actualizar proyecto";
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Eliminar proyecto
  const handleDelete = async () => {
    if (!selectedProyecto) return;
    
    try {
      setLoading(true);
      await deleteProyecto(selectedProyecto.ProyectoBaan);
      await loadProyectos(searchTerm);
      setDeleteModalOpen(false);
      setSelectedProyecto(null);
      return { success: true };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || "Error al eliminar proyecto";
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Funciones para abrir modals
  const openCreateModal = () => {
    setFormMode("create");
    setSelectedProyecto(null);
    setFormModalOpen(true);
  };

  const openEditModal = (proyecto) => {
    setFormMode("edit");
    setSelectedProyecto(proyecto);
    setFormModalOpen(true);
  };

  const openDeleteModal = (proyecto) => {
    setSelectedProyecto(proyecto);
    setDeleteModalOpen(true);
  };

  // Funciones para cerrar modals
  const closeFormModal = () => {
    setFormModalOpen(false);
    setSelectedProyecto(null);
    setError(null);
  };

  const closeDeleteModal = () => {
    setDeleteModalOpen(false);
    setSelectedProyecto(null);
    setError(null);
  };

  return {
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
  };
}