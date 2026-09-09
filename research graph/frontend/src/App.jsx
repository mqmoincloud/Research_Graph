import { Navigate, Route, Routes, useOutletContext } from 'react-router-dom'

import { getToken } from './api/client'
import Layout from './components/Layout'
import AdminUsers from './pages/AdminUsers'
import Login from './pages/Login'
import PrepGraph from './pages/PrepGraph'
import Profile from './pages/Profile'
import Signup from './pages/Signup'

// Routes re-runs this on every navigation, so the token is read fresh each
// time. Reading it in App instead would only happen on the first render, and
// logging in would not be noticed until the page was reloaded by hand.
function Protected() {
  return getToken() ? <Layout /> : <Navigate to="/login" />
}

// The users page is admin-only. The role comes from Layout, which got it from
// /me - not from anything the browser stores. Even so this only hides the
// screen; the API returns 403 to a plain user regardless, and THAT is where
// the rule actually lives.
function AdminOnly({ children }) {
  const user = useOutletContext()
  return user.role === 'admin' ? children : <Navigate to="/" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Everything inside here shares the top bar, and the login check is
          written once instead of on every single route. */}
      <Route element={<Protected />}>
        <Route path="/" element={<PrepGraph />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/users" element={<AdminOnly><AdminUsers /></AdminOnly>} />
      </Route>

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}
