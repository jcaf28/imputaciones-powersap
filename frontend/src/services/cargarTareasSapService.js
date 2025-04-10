// PATH: frontend/src/services/cargarTareasSapService.js
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * 1) Valida el archivo y devuelve { message, token }
 */
export async function validateSapFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${BASE_URL}/cargar-tareas-sap/validate-file`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  // La respuesta deberá ser { message: "Archivo válido", token: "..."}
  return response.data; 
}

/**
 * 2) Inicia el proceso SSE usando el token devuelto por validateSapFile
 */
export async function startSapProcess(token) {
  // Mandamos un POST sin archivo, sólo param
  const response = await axios.post(
    `${BASE_URL}/cargar-tareas-sap/start?token=${token}`
  );
  // Respuesta: { process_id: "..." }
  return response.data;
}

/**
 * 3) Cancela el proceso SSE
 */
export async function cancelSapProcess(processId) {
  const response = await axios.post(
    `${BASE_URL}/cargar-tareas-sap/cancel/${processId}`
  );
  return response.data;
}
