// PATH: frontend/src/hooks/useImputacionesIP.js

import { useState, useEffect } from "react";
import useSSE from "./useSSE";
import {
  validateImputacionFile,
  startImputacionesProcess,
  cancelImputacionesProcess,
} from "../services/uploadImputacionesService";

export default function useImputacionesIP() {
  // 1) Estados para los 4 archivos y si están validados
  const [files, setFiles] = useState([null, null, null, null]);
  const [validations, setValidations] = useState([false, false, false, false]);

  // 2) Estado del proceso
  const [processId, setProcessId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState("idle"); // "idle"|"in-progress"|"completed"|"cancelled"|"error"
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // 3) SSE
  const sseUrl = processId
    ? `${import.meta.env.VITE_API_BASE_URL}/imputaciones-ip/events/${processId}`
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
   * setFile: actualiza el i-ésimo archivo y reinicia su validación
   */
  function setFile(index, file) {
    const newFiles = [...files];
    newFiles[index] = file;
    setFiles(newFiles);

    const newVals = [...validations];
    newVals[index] = false; // reset validación
    setValidations(newVals);
  }

  /**
   * validateFile: llama al backend para validar este archivo (fake OK)
   */
  async function validateFile(index) {
    const file = files[index];
    if (!file) return;

    try {
      // Aquí podría haber lógica de "comprobar .xlsx" en frontend
      if (!file.name.endsWith(".xlsx")) {
        throw new Error("Debe ser un archivo .xlsx");
      }

      // Llamada al backend (fake por ahora)
      await validateImputacionFile(file, index);
      // Marcar validado
      const newVals = [...validations];
      newVals[index] = true;
      setValidations(newVals);
    } catch (err) {
      alert("Error validando el archivo: " + err.message);
    }
  }

  /**
   * canGenerate: solo se puede generar si las 4 validaciones son true
   */
  const canGenerate = validations.every((val) => val === true);

  /**
   * handleGenerate: inicia el proceso SSE en backend con los 4 archivos
   */
  async function handleGenerate() {
    if (!canGenerate) return;
    try {
      setIsUploading(true);
      const { process_id } = await startImputacionesProcess(files);
      setProcessId(process_id);
      setStatus("in-progress");
      setMessage("Iniciando proceso...");
    } catch (err) {
      alert("Error al iniciar proceso: " + err.message);
    } finally {
      setIsUploading(false);
    }
  }

  /**
   * handleCancel: cancela el proceso SSE
   */
  async function handleCancel() {
    if (!processId) return;
    await cancelImputacionesProcess(processId);
    setProcessId(null);
    setStatus("idle");
    setMessage("");
    setError("");
  }

  /**
   * handleDownload: descarga el resultado final
   */
  function handleDownload() {
    if (!processId) return;
    window.open(
      `${import.meta.env.VITE_API_BASE_URL}/imputaciones-ip/download/${processId}`,
      "_blank"
    );
  }

  return {
    files,
    validations,
    setFile,
    validateFile,
    canGenerate,
    isUploading,
    status,
    message,
    error,
    handleGenerate,
    handleCancel,
    handleDownload,
  };
}
