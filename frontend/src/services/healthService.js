import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL; 
// p.ej. "/powersap/api"

export async function getHealth() {
  const res = await axios.get(`${API_BASE_URL}/health`);
  return res.data;
}