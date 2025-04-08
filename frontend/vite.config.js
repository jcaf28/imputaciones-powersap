// PATH: frontend/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(() => {
  const serviceName = process.env.VITE_SERVICE_NAME;       
  const frontendPort = parseInt(process.env.VITE_FRONTEND_PORT); 
  const backendPort = parseInt(process.env.VITE_BACKEND_PORT);  

  return {
    define: {
      'import.meta.env.VITE_SERVICE_NAME': JSON.stringify(serviceName),
      'import.meta.env.VITE_FRONTEND_PORT': JSON.stringify(frontendPort),
      'import.meta.env.VITE_BACKEND_PORT': JSON.stringify(backendPort),
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(`/${serviceName}/api`),
    },

    base: `/${serviceName}/`,
    plugins: [react()],
    // Configuración del servidor de DESARROLLO de Vite
    server: {
      // Define un proxy para redirigir peticiones de /{serviceName}/api al backend correspondiente
      proxy: {
        [`/${serviceName}/api`]: {
          target: `http://${serviceName}-backend:${backendPort}`, // Redirige a backend en Docker
          changeOrigin: true, // Cambia el origen del host en la cabecera para evitar problemas CORS. Sin esto, la petición iría al mismo origen que el frontend (localhost:{forntendPort}, en vez de http://{serviceName}-backend:{backendPort}).
        },
      },
    },
  };
});
