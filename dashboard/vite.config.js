import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy /api requests to the Vercel serverless functions in dev
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
  // Expose environment variables to the client (only VITE_ prefixed ones are exposed)
  define: {
    'import.meta.env.VITE_API_MODE': JSON.stringify(process.env.VERCEL ? 'production' : 'development'),
  },
})
