// PATH: frontend/vite.config.js
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // ⚠️ loadEnv carga las variables del entorno del sistema (como ENV VITE_...)
  const env = loadEnv(mode, process.cwd(), '');

  const serviceName = env.VITE_SERVICE_NAME;
  const frontendPort = parseInt(env.VITE_FRONTEND_PORT);
  const backendPort = parseInt(env.VITE_BACKEND_PORT);

  return {
    base: `/${serviceName}/`,
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: frontendPort,
      proxy: {
        '/api': {
          target: `http://${serviceName}-backend:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});
