// PATH: frontend/src/hooks/useCargarRespuestaSap.js

import { useState, useEffect } from "react";
import {
  validateRespuestaSapFile,
  startRespuestaSapProcess,
  cancelRespuestaSapProcess,
  discardRespuestaSapFile,
} from "../services/cargarRespuestaSapService";
import useSSE from "./useSSE";

export default function useCargarRespuestaSap() {
  // ---------- 1) archivo y validación ----------
  const [file, setFile]             = useState(null);
  const [token, setToken]           = useState(null);
  const [validated, setValidated]   = useState(false);

  // ---------- 2) proceso ----------
  const [processId, setProcessId]   = useState(null);
  const [isUploading, setUploading] = useState(false);
  const [status, setStatus]         = useState("idle");      // idle|in-progress|completed|cancelled|error
  const [error, setError]           = useState("");
  const [logs, setLogs]             = useState([]);

  // ---------- 3) SSE ----------
  const sseUrl = processId ? `${import.meta.env.VITE_API_BASE_URL}/cargar-respuesta-sap/events/${processId}` : null;
  const { events } = useSSE(sseUrl);

  useEffect(() => {
    if (events.length === 0) return;
    const { type, data } = events.at(-1);

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

  // ---------- 4) helpers ----------
  async function validateFileHandler() {
    if (!file) return;
    try {
      const { token } = await validateRespuestaSapFile(file);
      setToken(token);
      setValidated(true);
    } catch (err) {
      alert(err.response?.data?.detail ?? err.message);
      setValidated(false);
    }
  }

  async function startProcess() {
    if (!validated) return alert("Primero valida el archivo");
    try {
      setUploading(true);
      setLogs(["Iniciando proceso…"]);
      const { process_id } = await startRespuestaSapProcess(token);
      setProcessId(process_id);
      setStatus("in-progress");
    } catch (err) {
      alert(err.response?.data?.detail ?? err.message);
    } finally {
      setUploading(false);
    }
  }

  async function cancelProcess() {
    if (!processId) return;
    await cancelRespuestaSapProcess(processId);
    setProcessId(null);
    setStatus("cancelled");
    setLogs(prev => [...prev, "Proceso cancelado por el usuario."]);
  }

  async function discardFile() {
    if (!token) return;
    await discardRespuestaSapFile(token);
    reset();
  }

  function reset() {
    setFile(null);
    setToken(null);
    setValidated(false);
    setProcessId(null);
    setStatus("idle");
    setError("");
    setLogs([]);
  }

  return {
    file, validated, isUploading, status, error, logs,
    setFile, validateFileHandler, startProcess, cancelProcess, discardFile,
  };
}
