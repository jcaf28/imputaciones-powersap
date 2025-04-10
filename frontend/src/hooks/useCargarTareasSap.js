// PATH: frontend/src/hooks/useCargarTareasSap.js

import { useState, useEffect } from "react";
import { validateSapFile, startSapProcess, cancelSapProcess } from "../services/cargarTareasSapService";
import useSSE from "./useSSE";

export default function useCargarTareasSAP() {
  // 1) Estados para el archivo y su validación
  const [file, setFile] = useState(null);
  const [validated, setValidated] = useState(false);

  // 2) Estado del proceso SSE
  const [processId, setProcessId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState("idle"); // "idle"|"in-progress"|"completed"|"cancelled"|"error"
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

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
        setMessage(data);
        break;
      case "completed":
        setStatus("completed");
        setMessage(data);
        break;
      case "cancelled":
        setStatus("cancelled");
        setMessage(data);
        break;
      case "error":
        setStatus("error");
        setError(data);
        break;
      default:
        break;
    }
  }, [events]);

  // ============== FUNCIONES ==============
  /**
   * setFileHandler: actualiza el archivo y reinicia la validación
   */
  function setFileHandler(newFile) {
    setFile(newFile);
    setValidated(false);
  }

  /**
   * validateFile: llama al backend para verificar columnas
   */
  async function validateFileHandler() {
    if (!file) return;
    try {
      await validateSapFile(file);
      setValidated(true);
    } catch (err) {
      alert("Error validando el archivo: " + err.response?.data?.detail ?? err.message);
      setValidated(false);
    }
  }

  /**
   * handleStartProcess: inicia el proceso SSE en backend con el archivo
   */
  async function handleStartProcess() {
    if (!validated) {
      alert("No puedes generar si el archivo no está validado");
      return;
    }
    try {
      setIsUploading(true);
      const { process_id } = await startSapProcess(file);
      setProcessId(process_id);
      setStatus("in-progress");
      setMessage("Iniciando proceso...");
    } catch (err) {
      alert("Error al iniciar proceso: " + err.response?.data?.detail ?? err.message);
    } finally {
      setIsUploading(false);
    }
  }

  /**
   * handleCancel: cancela el proceso SSE
   */
  async function handleCancel() {
    if (!processId) return;
    await cancelSapProcess(processId);
    setProcessId(null);
    setStatus("idle");
    setMessage("");
    setError("");
  }

  // Podrías añadir un handleDownload si tu backend devolviese un archivo resultante,
  // pero en este caso no es necesario.

  return {
    file,
    validated,
    isUploading,
    status,
    message,
    error,
    setFileHandler,
    validateFileHandler,
    handleStartProcess,
    handleCancel,
  };
}
