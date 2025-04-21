// PATH: frontend/src/services/obtenerFeedbackService.js

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * 1) Valida el archivo de feedback y devuelve { message, token }
 */
export async function validateFeedbackFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${BASE_URL}/obtener-feedback/validate-file`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data; // { message, token }
}

/**
 * 2) Inicia el proceso SSE usando el token devuelto por validateFeedbackFile.
 *    Devuelve { process_id }
 */
export async function startFeedbackProcess(token) {
  const response = await axios.post(
    `${BASE_URL}/obtener-feedback/start?token=${token}`
  );
  return response.data; // { process_id }
}

/**
 * 3) Cancela el proceso en curso.
 */
export async function cancelFeedbackProcess(processId) {
  const response = await axios.post(
    `${BASE_URL}/obtener-feedback/cancel/${processId}`
  );
  return response.data;
}
