// One axios instance for the whole app.
// baseURL is left empty -> requests go to the same origin ("/api/...")
// and the Vite dev server forwards them to FastAPI (http://127.0.0.1:8000).
// When deploying, set VITE_API_BASE_URL in .env.

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,   // the graph takes 1-3 minutes
})

// We pull the backend error message out and throw a plain Error,
// so showing just err.message in the UI is enough.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail
    const message =
      (typeof detail === 'string' && detail) ||
      err.response?.statusText ||
      'Could not connect to the backend. Is the API running?'
    return Promise.reject(new Error(message))
  },
)

export default api
