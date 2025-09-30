import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Use IPv4 to avoid ::1 (IPv6 localhost) when backend listens on IPv4 only
      '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true },
      '/news': { target: 'http://127.0.0.1:8080', changeOrigin: true }
    }
  }
})
