import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getTiposOrdenes() {
  const res = await axios.get(`${API_BASE_URL}/tipos-ordenes`);
  return res.data;
}
