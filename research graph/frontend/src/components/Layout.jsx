import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { removeToken, setUnauthorisedHandler } from '../api/client'
import { getMe } from '../api/auth'

export default function Layout() {
  const navigate = useNavigate()

  // Who is logged in, asked of the server rather than kept in localStorage.
  // Anything stored in the browser can be edited by whoever is sitting at it,
  // so the role has to come from /me on every load.
  const [user, setUser] = useState(null)

  // One place that reacts to an expired token, instead of every page having
  // its own copy. The axios interceptor calls this on any 401.
  useEffect(() => {
    setUnauthorisedHandler(() => navigate('/login'))
    return () => setUnauthorisedHandler(null)
  }, [navigate])

  // Bumped by a page that changed something /me returns, so this asks again.
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    async function loadMe() {
      try {
        setUser(await getMe())
      } catch {
        // A 401 has already cleared the token in the interceptor; anything
        // else (server down) is not something this screen can recover from.
        removeToken()
        navigate('/login')
      }
    }

    loadMe()
  }, [navigate, refresh])

  function handleLogout() {
    removeToken()
    navigate('/login')
  }

  // NavLink gives us isActive, so the page you are on is marked.
  function linkClass({ isActive }) {
    return isActive ? 'nav-link nav-link-on' : 'nav-link'
  }

  // Nothing renders until we know who this is, otherwise the admin-only page
  // would flash past its guard while user is still null.
  if (!user) {
    return <p className="page">Loading...</p>
  }

  return (
    <>
      <nav className="topbar">
        <div className="topbar-inner">
          <span className="brand">Prep Graph</span>

          <NavLink to="/" className={linkClass} end>Research</NavLink>
          <NavLink to="/profile" className={linkClass}>Profile</NavLink>
          {user.role === 'admin' && (
            <NavLink to="/users" className={linkClass}>Users</NavLink>
          )}

          <div className="topbar-right">
            <span className="who">
              {user.name}
              <span className="tag">{user.role}</span>
            </span>
            <button onClick={handleLogout} className="link">Log out</button>
          </div>
        </div>
      </nav>

      {/* reloadUser lets Profile refresh the name in the bar after saving. */}
      <Outlet context={{ ...user, reloadUser: () => setRefresh((n) => n + 1) }} />
    </>
  )
}
