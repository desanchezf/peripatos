import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En Docker el backend es http://backend:8000; fuera de Docker, el puerto publicado
const backend = process.env.BACKEND_URL ?? 'http://localhost:8001'

export default defineConfig({
  plugins: [react()],
  server: {
    // Mismo origen para el navegador: la sesión y el CSRF de Django funcionan sin CORS
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '^/admin/': { target: backend, changeOrigin: true },
      '/static': { target: backend, changeOrigin: true },
      '/private': { target: backend, changeOrigin: true },
    },
  },
})
