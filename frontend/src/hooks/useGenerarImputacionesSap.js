// PATH: frontend/src/hooks/useGenerarImputacionesSap.js

import { useState, useEffect, useCallback } from "react";
import {
  fetchPendingImputaciones,
  startGenerarImputacionesSap,
  cancelGenerarImputacionesSap,
  downloadGeneratedCSV
} from "../services/generarImputacionesSapService";
import useSSE from "./useSSE";

export default function useGenerarImputacionesSap() {
  // ===================== ESTADOS =====================
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [processId, setProcessId] = useState(null);
  const [status, setStatus] = useState("idle"); // 'in-progress', 'completed', 'cancelled', 'error'
  const [logs, setLogs] = useState([]);

  // ===================== COLUMNAS =====================
  const columns = [
    { field: "id", headerName: "ID", width: 90 },
    {
      field: "fechaImp",
      headerName: "Fecha Imp.",
      width: 140,
      valueFormatter: (params) => {
        if (!params.value) return "";
        const date = new Date(params.value);
        return date.toLocaleDateString();
      }
    },
    { field: "codEmpleado", headerName: "Empleado", width: 130 },
    { field: "horas", headerName: "Horas", width: 90, type: "number" },
    { field: "proyecto", headerName: "Proyecto", width: 150 },
    { field: "tipoCoche", headerName: "Tipo Coche", width: 120 },
    { field: "cargadoSap", headerName: "Cargado SAP?", width: 120, type: "boolean" }
  ];

  // ===================== SSE URL & HOOK =====================
  const sseUrl = processId
    ? `${import.meta.env.VITE_API_BASE_URL}/generar-imputaciones-sap/events/${processId}`
    : null;
  const { events } = useSSE(sseUrl);

  // Interpretar SSE
  useEffect(() => {
    if (events.length === 0) return;
    const lastEvent = events[events.length - 1];
    const { type, data } = lastEvent;

    switch (type) {
      case "message":
        setStatus("in-progress");
        setLogs((prev) => [...prev, data]);
        break;
      case "completed":
        setStatus("completed");
        setLogs((prev) => [...prev, `✅ ${data}`]);
        break;
      case "cancelled":
        setStatus("cancelled");
        setLogs((prev) => [...prev, `🛑 ${data}`]);
        break;
      case "error":
        setStatus("error");
        setLogs((prev) => [...prev, `❌ ${data}`]);
        setError(data);
        break;
      default:
        break;
    }
  }, [events]);

  // ===================== CARGAR DATOS TABLA =====================
  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchPendingImputaciones();
      setRows(data);
    } catch (err) {
      setError(err.message || "Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    loadData();
  }, [loadData]);

  // ===================== ACCIONES =====================
  async function handleStartProcess() {
    try {
      setLoading(true);
      setLogs(["Iniciando proceso de generación SAP..."]);
      setError("");
      const { process_id } = await startGenerarImputacionesSap();
      setProcessId(process_id);
      setStatus("in-progress");
    } catch (err) {
      setError(err.message || "Error al iniciar proceso");
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    if (!processId) return;
    try {
      await cancelGenerarImputacionesSap(processId);
      setStatus("idle");
      setError("");
      setLogs((prev) => [...prev, "Proceso cancelado por el usuario."]);
      setProcessId(null);
    } catch (err) {
      setError(err.message || "Error al cancelar");
    }
  }

  async function downloadCSV() {
    if (!processId) return;
    await downloadGeneratedCSV(processId);
  }

  function refreshData() {
    loadData();
  }

  /**
   * resetHook: restablece todos los estados al valor inicial.
   * Útil si te sales y entras de la página, pero tu routing
   * no desmonta el componente y quieres forzar "limpieza".
   */
  function resetHook() {
    setRows([]);
    setLoading(false);
    setError("");
    setProcessId(null);
    setStatus("idle");
    setLogs([]);
  }

  // ===================== RETORNO =====================
  return {
    // estados
    rows,
    columns,
    loading,
    error,
    status,
    logs,
    processId,
    // acciones
    handleStartProcess,
    handleCancel,
    downloadCSV,
    refreshData,
    // extra
    resetHook
  };
}
