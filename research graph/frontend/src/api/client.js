// One axios instance for the whole app.
// baseURL khaali rakha hai -> requests same origin par jaati hain ("/api/...")
// aur Vite dev server unhe FastAPI (http://127.0.0.1:8000) ko forward kar deta hai.
// Deploy karte waqt .env mein VITE_API_BASE_URL set kar dena.

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,   // graph 1-3 minute leta hai
})

// Backend ka error message nikaal kar ek simple Error throw karte hain,
// taake UI mein sirf err.message dikhana kaafi ho.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail
    const message =
      (typeof detail === 'string' && detail) ||
      err.response?.statusText ||
      'Backend se connect nahi ho paaya. Kya API chal rahi hai?'
    return Promise.reject(new Error(message))
  },
)

export default api
