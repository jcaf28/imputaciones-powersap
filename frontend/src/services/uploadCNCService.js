// PATH: frontend/src/services/uploadCNCService.js

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function startCNCProcess(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(`${API_BASE_URL}/obtencion-cnc/start`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data; // { process_id: '...' }
}

export async function cancelCNCProcess(processId) {
  await axios.post(`${API_BASE_URL}/obtencion-cnc/cancel/${processId}`);
}
