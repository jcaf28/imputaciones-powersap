// PATH: frontend/src/services/healthService.js

import axios from "axios";

export async function getHealth() {
  const res = await axios.get(`/api/health`);
  return res.data;
}