// PATH: frontend/src/hooks/useObtenerFeedback.js

import { useState, useEffect } from "react";
import {
  validateFeedbackFile,
  startFeedbackProcess,
  cancelFeedbackProcess,
} from "../services/obtenerFeedbackService";
import useSSE from "./useSSE";

export default function useObtenerFeedback() {
  // ---------- 1. archivo + validación ----------
  const [file, setFile] = useState(null);
  const [token, setToken] = useState(null);
  const [validated, setValidated] = useState(false);

  // ---------- 2. proceso / SSE ----------
  const [processId, setProcessId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | in-progress | completed | cancelled | error
  const [error, setError] = useState("");
  const [logs, setLogs] = useState([]);
  const [downloadUrl, setDownloadUrl] = useState(null); // 👈 nuevo

  // ---------- 3. SSE ----------
  const sseUrl = processId
    ? `${import.meta.env.VITE_API_BASE_URL}/obtener-feedback/events/${processId}`
    : null;
  const { events } = useSSE(sseUrl);

  useEffect(() => {
    if (!events.length) return;

    const { type, data } = events[events.length - 1];

    switch (type) {
      case "message":
        setStatus("in-progress");
        setLogs((prev) => [...prev, data]);
        break;
      case "completed":
        setStatus("completed");
        setLogs((prev) => [...prev, `✅ ${data}`]);
        // 👉 genera la URL de descarga
        setDownloadUrl(
          `${import.meta.env.VITE_API_BASE_URL}/obtener-feedback/download/${processId}`
        );
        break;
      case "cancelled":
        setStatus("cancelled");
        setLogs((prev) => [...prev, `🛑 ${data}`]);
        break;
      case "error":
        setStatus("error");
        setError(data);
        setLogs((prev) => [...prev, `❌ Error: ${data}`]);
        break;
      default:
        break;
    }
  }, [events, processId]);

  // ---------- 4. helpers ----------
  async function handleValidate() {
    if (!file) return;
    try {
      const { token } = await validateFeedbackFile(file);
      setToken(token);
      setValidated(true);
    } catch (err) {
      alert(
        "Error validando el archivo: " +
          (err.response?.data?.detail ?? err.message)
      );
      setValidated(false);
      setToken(null);
    }
  }

  async function handleStart() {
    if (!validated) {
      alert("El archivo debe estar validado antes de iniciar el proceso.");
      return;
    }
    try {
      setIsUploading(true);
      setLogs(["Iniciando proceso..."]);
      const { process_id } = await startFeedbackProcess(token);
      setProcessId(process_id);
      setStatus("in-progress");
      setDownloadUrl(null); // limpia cualquier url previa
    } catch (err) {
      alert(
        "Error al iniciar proceso: " +
          (err.response?.data?.detail ?? err.message)
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleCancel() {
    if (!processId) return;
    await cancelFeedbackProcess(processId);
    setProcessId(null);
    setStatus("idle");
    setError("");
    setDownloadUrl(null);
    setLogs((prev) => [...prev, "Proceso cancelado por el usuario."]);
  }

  return {
    file,
    validated,
    status,
    error,
    isUploading,
    logs,
    downloadUrl,           // 👈 exporta la url
    // handlers
    setFile,
    validateFile: handleValidate,
    startProcess: handleStart,
    cancelProcess: handleCancel,
  };
}
