import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server /api ko FastAPI backend par bhej deta hai, taaki browser ko
// kabhi cross-origin request na karni pade.
//
// DHYAN DO: vite.config.js ke andar `process.env` mein .env file ki values
// AUTOMATIC nahi aati. Uske liye loadEnv() call karna padta hai. Pehle yahan
// sirf process.env padha ja raha tha, isliye .env ka VITE_PROXY_TARGET kabhi
// use hi nahi hota tha - hamesha neeche wala default chalta tha.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  console.log(`[vite] /api  ->  ${target}`)

  return {
    plugins: [react()],
    server: {
      // strictPort ZAROORI hai. Iske bina Vite chupchaap agla khaali port
      // le leta hai (5173 busy -> 5174 -> ... -> 5181), aur pata hi nahi
      // chalta ki tum kaunsa app khol rahe ho. Ek baar aisa hi hua tha -
      // 5173 par kisi doosre project ka Vite chal raha tha.
      // Ab port busy hoga to Vite saaf error dega, chupchaap khiskega nahi.
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
