// PATH: frontend/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(() => {
  // Lee las variables de entorno definidas en Docker (ENV).
  const serviceName = process.env.VITE_SERVICE_NAME;
  const frontendPort = parseInt(process.env.VITE_FRONTEND_PORT);
  const backendPort = parseInt(process.env.VITE_BACKEND_PORT);

  return {
    define: {
      // inyectar en import.meta.env
      'import.meta.env.VITE_SERVICE_NAME': JSON.stringify(serviceName),
      'import.meta.env.VITE_FRONTEND_PORT': JSON.stringify(frontendPort),
      'import.meta.env.VITE_BACKEND_PORT': JSON.stringify(backendPort),
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(`/${serviceName}/api`),
    },
    base: `/${serviceName}/`,
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `http://${serviceName}-backend:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
    
  };
});
