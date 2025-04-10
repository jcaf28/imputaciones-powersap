// PATH: frontend/src/services/cargarTareasSapService.js

import axios from "axios";

// Base URL, p. ej. VITE_API_BASE_URL="http://localhost:8000/mi-servicio/api"
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function validateSapFile(file) {
  // Endpoint POST /cargar-tareas-sap/validate-file
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
  return response.data; 
}

export async function startSapProcess(file) {
  // Endpoint POST /cargar-tareas-sap/start
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${BASE_URL}/cargar-tareas-sap/start`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data; // debería devolver { process_id }
}

export async function cancelSapProcess(processId) {
  // Endpoint POST /cargar-tareas-sap/cancel/{process_id}
  const response = await axios.post(
    `${BASE_URL}/cargar-tareas-sap/cancel/${processId}`
  );
  return response.data;
}
