// PATH: frontend/src/services/proyectosService.js

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Obtiene la lista de proyectos con opciones de paginación y búsqueda
 */
export async function fetchProyectos(params = {}) {
  const { skip = 0, limit = 100, search = "" } = params;
  
  const queryParams = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
    ...(search && { search })
  });

  const response = await axios.get(`${BASE_URL}/proyectos?${queryParams}`);
  return response.data;
}

/**
 * Obtiene un proyecto específico por su ProyectoBaan
 */
export async function fetchProyecto(proyectoBaan) {
  const response = await axios.get(`${BASE_URL}/proyectos/${encodeURIComponent(proyectoBaan)}`);
  return response.data;
}

/**
 * Crea un nuevo proyecto
 */
export async function createProyecto(proyectoData) {
  const response = await axios.post(`${BASE_URL}/proyectos`, proyectoData);
  return response.data;
}

/**
 * Actualiza un proyecto existente
 */
export async function updateProyecto(proyectoBaan, proyectoData) {
  const response = await axios.put(
    `${BASE_URL}/proyectos/${encodeURIComponent(proyectoBaan)}`, 
    proyectoData
  );
  return response.data;
}

/**
 * Elimina un proyecto
 */
export async function deleteProyecto(proyectoBaan) {
  const response = await axios.delete(`${BASE_URL}/proyectos/${encodeURIComponent(proyectoBaan)}`);
  return response.data;
}