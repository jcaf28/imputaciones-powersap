// PATH: frontend/vite.config.js

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const base = `/${env.SERVICE_NAME}/`;

  return {
    base,
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: `http://${env.SERVICE_NAME}-backend:8000`,
          changeOrigin: true,
        },
      },
    },
  };
});
