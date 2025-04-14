// PATH: frontend/src/services/generarImputacionesSapService.js

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * 1) GET: Obtener imputaciones pendientes
 */
export async function fetchPendingImputaciones() {
  const resp = await axios.get(`${BASE_URL}/generar-imputaciones-sap/list`);
  return resp.data; // array de objetos
}

export async function fetchPendingImputacionesCount() {
  const resp = await axios.get(`${BASE_URL}/generar-imputaciones-sap/list-summary`);
  return resp.data.count;
}

/**
 * 2) POST: Iniciar proceso SSE (devuelve process_id)
 */
export async function startGenerarImputacionesSap() {
  // Ajusta si necesitas query params, etc.
  const resp = await axios.post(`${BASE_URL}/generar-imputaciones-sap/start`);
  return resp.data; // { process_id: "..."}
}

/**
 * 3) POST: Cancelar proceso SSE
 */
export async function cancelGenerarImputacionesSap(processId) {
  const resp = await axios.post(`${BASE_URL}/generar-imputaciones-sap/cancel/${processId}`);
  return resp.data;
}

/**
 * 4) GET/POST: Descargar CSV final
 *    - Podrías usar GET si tu backend expone /download/{processId}
 */
export async function downloadGeneratedCSV(processId) {
  // Descarga CSV. Suponemos que el backend genera un CSV en memoria y lo expone en:
  // GET /generar-imputaciones-sap/download/{processId}
  const url = `${BASE_URL}/generar-imputaciones-sap/download/${processId}`;

  // Forzar descarga
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.click();
}
