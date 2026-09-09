import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { login } from '../api/auth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  // Set while the form is in flight, so a second click cannot send a second
  // copy of the same request.
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (saving) return

    const cleanEmail = email.trim()

    if (!cleanEmail) {
      setError('Email is required.')
      return
    }

    if (!EMAIL_RE.test(cleanEmail)) {
      setError('Enter a valid email address.')
      return
    }

    // Only the *all spaces* case is rejected. The password itself is sent
    // untrimmed, because a space can be a real character inside one.
    if (!password.trim()) {
      setError('Password is required.')
      return
    }

    setError('')
    setSaving(true)

    try {
      await login(cleanEmail, password)
      navigate('/')
    } catch (err) {
      // The API gives the same message for a wrong password and an unknown
      // email on purpose, so we do not guess which one it was either.
      setError(err.status === 401 ? 'Invalid email or password.' : err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h1 className="auth-title">Prep Graph</h1>

        <form onSubmit={handleSubmit} className="card">
          <label className="field-label" htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="field"
          />

          <label className="field-label" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="field"
          />

          {error && <p className="error-text">{error}</p>}

          <button type="submit" disabled={saving} className="primary wide">
            {saving ? 'Signing in...' : 'Log in'}
          </button>
        </form>

        <p className="auth-foot">
          No account? <Link to="/signup" className="accent-link">Sign up</Link>
        </p>
      </div>
    </div>
  )
}
