import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server sends /api on to the FastAPI backend, so the browser never
// has to make a cross-origin request.
//
// NOTE: inside vite.config.js, `process.env` does NOT AUTOMATICALLY carry the
// values from the .env file. loadEnv() has to be called for that. Earlier only
// process.env was read here, so VITE_PROXY_TARGET from .env was never actually
// used - the default below always won.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  console.log(`[vite] /api  ->  ${target}`)

  return {
    plugins: [react()],
    server: {
      // strictPort is ESSENTIAL. Without it Vite quietly takes the next free
      // port (5173 busy -> 5174 -> ... -> 5181), and there is no telling
      // which app you are opening. That happened once - another
      // project's Vite was running on 5173.
      // Now if the port is busy Vite errors clearly instead of sliding away.
      port: 5200,
      strictPort: true,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
        },
      },
    },
  }
})
