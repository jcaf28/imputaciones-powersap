// PATH: frontend/src/hooks/useCNC.js

import { useState, useEffect } from "react";
import { startCNCProcess, cancelCNCProcess } from "../services/uploadCNCService";
import useSSE from "./useSSE";

/**
 * Hook que encapsula toda la lógica de "Ejemplo CNC":
 * - Mantenimiento de 'file' (el Excel)
 * - Subida y obtención de processId
 * - Conexión SSE para saber el estado del proceso
 * - Manejo de cancelación y descarga de resultados
 */
export default function useCNC() {
  // 1) Estado del archivo y del processId
  const [file, setFile] = useState(null);
  const [processId, setProcessId] = useState(null);

  // 2) Flag para saber si estamos subiendo el archivo (antes de tener processId)
  const [isUploading, setIsUploading] = useState(false);

  // 3) Preparar la URL SSE (solo si tenemos processId)
  const url = processId
    ? `${import.meta.env.VITE_API_BASE_URL}/obtencion-cnc/events/${processId}`
    : null;

  // 4) Conectarse por SSE a esa URL
  const { events } = useSSE(url);

  // 5) Estados de control del proceso (status, mensaje, error)
  const [status, setStatus] = useState("idle"); // "idle" | "in-progress" | "completed" | "cancelled" | "error"
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // 6) Efecto para interpretar los eventos SSE y actualizar status / message / error
  useEffect(() => {
    if (events.length === 0) return;

    // Tomamos el último evento
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
        // Caso no contemplado
        break;
    }
  }, [events]);

  // ============= Funciones públicas que el componente que usa este hook va a invocar =============

  /**
   * handleStart: subir el archivo al backend y obtener processId
   */
  function handleStart() {
    if (!file) return;

    setIsUploading(true);
    startCNCProcess(file)
      .then(({ process_id }) => {
        setProcessId(process_id);
      })
      .catch((err) => {
        alert("Error al iniciar el proceso: " + err.message);
      })
      .finally(() => {
        // Independientemente del éxito o error, dejamos de "subir"
        setIsUploading(false);
      });
  }

  /**
   * handleCancel: solicitar la cancelación del proceso en el backend
   */
  async function handleCancel() {
    if (!processId) return;

    await cancelCNCProcess(processId);

    // Reiniciamos todo a estado inicial
    setProcessId(null);
    setStatus("idle");
    setMessage("");
    setError("");
  }

  /**
   * handleDownload: descargar el archivo final (el backend lo genera al "completed")
   */
  function handleDownload() {
    if (!processId) return;
    window.open(
      `${import.meta.env.VITE_API_BASE_URL}/obtencion-cnc/download/${processId}`,
      "_blank"
    );
  }

  // 7) Devolvemos los datos y funciones necesarios para componer la UI
  return {
    file,
    setFile,
    isUploading,
    status,
    message,
    error,
    handleStart,
    handleCancel,
    handleDownload,
  };
}
