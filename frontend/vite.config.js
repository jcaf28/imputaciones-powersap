// PATH: frontend/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: "/ip/",
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      "/api": {  
        target: "http://ip-backend:8000",
        changeOrigin: true,
      },
    },
  },
});
