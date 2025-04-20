// PATH: frontend/src/services/cargarRespuestaSapService.js

import axios from "axios";
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/* 1) validar */
export async function validateRespuestaSapFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await axios.post(`${BASE_URL}/cargar-respuesta-sap/validate-file`, formData);
  return res.data;          // { message, token }
}

/* 2) start */
export async function startRespuestaSapProcess(token) {
  const res = await axios.post(`${BASE_URL}/cargar-respuesta-sap/start?token=${token}`);
  return res.data;          // { process_id }
}

/* 3) cancel */
export async function cancelRespuestaSapProcess(processId) {
  const res = await axios.post(`${BASE_URL}/cargar-respuesta-sap/cancel/${processId}`);
  return res.data;
}

/* 4) descartar (opcional) */
export async function discardRespuestaSapFile(token) {
  const res = await axios.post(`${BASE_URL}/cargar-respuesta-sap/discard?token=${token}`);
  return res.data;
}
