import { useState, useEffect } from "react";
import { validateSapFile, startSapProcess, cancelSapProcess } from "../services/cargarTareasSapService";
import useSSE from "./useSSE";

export default function useCargarTareasSap() {
  // 1) Estados para el archivo y su validación
  const [file, setFile] = useState(null);
  const [token, setToken] = useState(null);
  const [validated, setValidated] = useState(false);

  // 2) Estado del proceso SSE
  const [processId, setProcessId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState("idle"); // "idle"|"in-progress"|"completed"|"cancelled"|"error"
  const [error, setError] = useState("");
  
  // NUEVO: en vez de un message único, mantenemos array de logs
  const [logs, setLogs] = useState([]);

  // 3) SSE: generamos la URL si tenemos un processId
  const sseUrl = processId
    ? `${import.meta.env.VITE_API_BASE_URL}/cargar-tareas-sap/events/${processId}`
    : null;
  const { events } = useSSE(sseUrl);

  // 4) Interpretar eventos SSE
  useEffect(() => {
    if (events.length === 0) return;

    const lastEvent = events[events.length - 1];
    const { type, data } = lastEvent;

    switch (type) {
      case "message":
        setStatus("in-progress");
        setLogs(prev => [...prev, data]);
        break;
      case "completed":
        setStatus("completed");
        setLogs(prev => [...prev, `✅ ${data}`]);
        break;
      case "cancelled":
        setStatus("cancelled");
        setLogs(prev => [...prev, `🛑 ${data}`]);
        break;
      case "error":
        setStatus("error");
        setError(data);
        setLogs(prev => [...prev, `❌ Error: ${data}`]);
        break;
      default:
        break;
    }
  }, [events]);

  // ============== FUNCIONES ==============
  function setFileHandler(newFile) {
    setFile(newFile);
    setValidated(false);
  }

  async function validateFileHandler() {
    if (!file) return;
    try {
      const response = await validateSapFile(file);
      setValidated(true);
      setToken(response.token); // 👈 asegúrate de que el backend lo devuelve
    } catch (err) {
      alert("Error validando el archivo: " + (err.response?.data?.detail ?? err.message));
      setValidated(false);
      setToken(null); // por si acaso
    }
  }

  async function handleStartProcess() {
    if (!validated) {
      alert("No puedes generar si el archivo no está validado");
      return;
    }
    try {
      setIsUploading(true);
      // Limpiar logs anteriores cada vez que arranca un proceso
      setLogs(["Iniciando proceso..."]);
      const { process_id } = await startSapProcess(token);
      setProcessId(process_id);
      setStatus("in-progress");
    } catch (err) {
      alert("Error al iniciar proceso: " + err.response?.data?.detail ?? err.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleCancel() {
    if (!processId) return;
    await cancelSapProcess(processId);
    setProcessId(null);
    setStatus("idle");
    setError("");
    // Conserva el log o limpialo, a gusto
    setLogs(prev => [...prev, "Proceso cancelado por el usuario."]);
  }

  return {
    file,
    validated,
    isUploading,
    status,
    error,
    logs,
    setFileHandler,
    validateFileHandler,
    handleStartProcess,
    handleCancel,
  };
}
