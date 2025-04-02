// PATH: frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(() => {
  const serviceName = import.meta.env.VITE_SERVICE_NAME
  const frontendPort = parseInt(import.meta.env.VITE_FRONTEND_PORT)
  
  return {
    base: `/${serviceName}/`,
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: frontendPort,
      proxy: {
        '/api': {
          // redirige a "serviceName-backend" dentro de la red Docker
          target: `http://${serviceName}-backend:${import.meta.env.VITE_BACKEND_PORT || 8000}`,
          changeOrigin: true,
        },
      },
    },
  }
})
