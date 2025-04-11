// PATH: frontend/src/services/agregarImputacionesService.js

import axios from "axios";

// Base URL
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * 1) Valida el archivo y devuelve { message, token }
 */
export async function validateImputacionesFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  // POST /agregar-imputaciones/validate-file
  const response = await axios.post(
    `${BASE_URL}/agregar-imputaciones/validate-file`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );
  // Respuesta: { message: "Archivo válido", token: "..." }
  return response.data;
}

/**
 * 2) Inicia el proceso SSE usando el token
 */
export async function startImputacionesProcess(token) {
  // POST /agregar-imputaciones/start?token=xxx
  const response = await axios.post(
    `${BASE_URL}/agregar-imputaciones/start?token=${token}`
  );
  return response.data; // { process_id: "..." }
}

/**
 * 3) Cancela el proceso SSE
 */
export async function cancelImputacionesProcess(processId) {
  // POST /agregar-imputaciones/cancel/{process_id}
  const response = await axios.post(
    `${BASE_URL}/agregar-imputaciones/cancel/${processId}`
  );
  return response.data;
}
