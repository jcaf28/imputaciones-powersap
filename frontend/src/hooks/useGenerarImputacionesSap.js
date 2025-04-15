// PATH: frontend/src/hooks/useGenerarImputacionesSap.js

import { useState, useEffect } from "react";
import {
  fetchPendingImputaciones,
  fetchPendingImputacionesCount,
  startGenerarImputacionesSap,
  cancelGenerarImputacionesSap,
  downloadGeneratedCSV
} from "../services/generarImputacionesSapService";

export default function useGenerarImputacionesSap() {
  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([
    { field: "id", headerName: "ID", width: 90 },
    { field: "fechaImp", headerName: "Fecha", width: 120 },
    { field: "codEmpleado", headerName: "Empleado", width: 120 },
    { field: "timpu", headerName: "Timpu", width: 100 },
    { field: "horas", headerName: "Horas", width: 100 },
    { field: "proyecto", headerName: "Proyecto", width: 130 },
    { field: "tipoCoche", headerName: "Tipo Coche", width: 120 },
    { field: "numCoche", headerName: "Nº Coche", width: 110 },
    { field: "centroTrabajo", headerName: "Centro Trabajo", width: 140 },
    { field: "tarea", headerName: "Tarea", width: 110 },
    { field: "tareaAsoc", headerName: "Tarea Asoc.", width: 130 },
    { field: "tipoIndirecto", headerName: "Tipo Indirecto", width: 140 },
    { field: "tipoMotivo", headerName: "Tipo Motivo", width: 120 },
    { field: "timestampInput", headerName: "Fecha Input", width: 160 },
    { field: "tipoImput", headerName: "Tipo Imput", width: 110 },
    { field: "areaTarea", headerName: "Area Tarea", width: 130 },
    { field: "area_id", headerName: "Area ID", width: 100 },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | in-progress | completed | error
  const [logs, setLogs] = useState([]);
  const [processId, setProcessId] = useState(null);
  const [rowCount, setRowCount] = useState(null);
  const [showingRows, setShowingRows] = useState(false);

  // Al montar, solo pedimos el conteo de imputaciones pendientes
  useEffect(() => {
    fetchPendingImputacionesCount()
      .then(setRowCount)
      .catch(() => setRowCount(null));
  }, []);

  // Mostrar registros por primera vez o refrescar si ya están visibles
  const toggleShowRows = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPendingImputaciones();
      setRows(data);
      setShowingRows(true); // aseguramos que quede activo
    } catch (err) {
      setError("Error al cargar registros");
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      const data = await fetchPendingImputaciones();
      setRows(data);
    } catch (err) {
      setError("Error al refrescar registros");
    }
  };

  const handleStartProcess = async () => {
    setLoading(true);
    setError(null);
    try {
      const { process_id } = await startGenerarImputacionesSap();
      setProcessId(process_id);
      setStatus("in-progress");
      setLogs([]);

      const evtSource = new EventSource(
        `${import.meta.env.VITE_API_BASE_URL}/generar-imputaciones-sap/events/${process_id}`
      );

      evtSource.onmessage = (event) => {
        setLogs((prevLogs) => [...prevLogs, event.data]);
      };

      evtSource.addEventListener("completed", (event) => {
        setLogs((prevLogs) => [...prevLogs, event.data]);
        setStatus("completed");
        evtSource.close();
      });

      evtSource.addEventListener("cancelled", (event) => {
        setLogs((prevLogs) => [...prevLogs, event.data]);
        setStatus("cancelled");
        evtSource.close();
      });

      evtSource.onerror = () => {
        setLogs((prevLogs) => [...prevLogs, "❌ Error de conexión SSE"]);
        setStatus("error");
        evtSource.close();
      };
    } catch (err) {
      setError("Error al iniciar el proceso");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!processId) return;
    await cancelGenerarImputacionesSap(processId);
  };

  const downloadCSV = () => {
      downloadGeneratedCSV();
  };

  return {
    rows,
    columns,
    loading,
    error,
    status,
    logs,
    processId,
    handleStartProcess,
    handleCancel,
    refreshData,
    downloadCSV,
    rowCount,
    showingRows,
    toggleShowRows
  };
}
