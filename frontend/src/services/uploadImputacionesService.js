// PATH: frontend/src/services/uploadImputacionesService.js

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Valida un archivo en el backend.
 */
export async function validateImputacionFile(file, index) {
  const formData = new FormData();
  formData.append("file", file);

  await axios.post(
    `${API_BASE_URL}/imputaciones-ip/validate-file?index=${index}`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
}

/**
 * Inicia el proceso SSE en backend subiendo los 4 archivos
 */
export async function startImputacionesProcess(files) {
  const formData = new FormData();
  // Añadimos cada archivo con un nombre distinto
  formData.append("file1", files[0]);
  formData.append("file2", files[1]);
  formData.append("file3", files[2]);
  formData.append("file4", files[3]);

  const response = await axios.post(`${API_BASE_URL}/imputaciones-ip/start`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data; // { process_id: '...' }
}

/**
 * Cancela el proceso SSE
 */
export async function cancelImputacionesProcess(processId) {
  await axios.post(`${API_BASE_URL}/imputaciones-ip/cancel/${processId}`);
}
