
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,   // the graph takes 1-3 minutes
})

// ---- the token ----------------------------------------------------------
// Kept in localStorage under "token", the same as CaseDesk. It survives a
// page reload, which sessionStorage would not.

export function getToken() {
  return localStorage.getItem('token')
}

export function saveToken(token) {
  localStorage.setItem('token', token)
}

export function removeToken() {
  localStorage.removeItem('token')
}

// A page can hand this in so that an expired token sends the user back to the
// login screen. Set once, in Layout, rather than in every page.
let onUnauthorised = null

export function setUnauthorisedHandler(handler) {
  onUnauthorised = handler
}

// Every request carries the token if we have one, as the standard
// "Authorization: Bearer <token>" header the backend's HTTPBearer expects.
api.interceptors.request.use((cfg) => {
  const token = getToken()
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`
  }
  return cfg
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status ?? 0

    if (status === 401) {
      removeToken()
      if (onUnauthorised) onUnauthorised()
    }

    const envelope = err.response?.data?.error

    // A field message is more useful than "Validation failed", so it wins.
    const fieldMessage = envelope && Object.values(envelope.fields || {})[0]

    const message =
      fieldMessage ||
      envelope?.message ||
      err.response?.statusText ||
      'Could not connect to the backend. Is the API running?'

    const error = new Error(message)
    error.status = status
    return Promise.reject(error)
  },
)

export default api
