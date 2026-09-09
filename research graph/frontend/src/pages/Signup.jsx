import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { login, signup } from '../api/auth'

export default function Signup() {
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (saving) return

    setError('')
    setSaving(true)

    try {
      await signup(name, email, password)
      // Straight in afterwards, so nobody has to type the same password twice.
      // Signup only creates the row; the token still has to come from /login.
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h1 className="auth-title">Prep Graph</h1>

        <form onSubmit={handleSubmit} className="card">
          <label className="field-label" htmlFor="signup-name">Name</label>
          <input
            id="signup-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="field"
          />

          <label className="field-label" htmlFor="signup-email">Email</label>
          <input
            id="signup-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="field"
          />

          <label className="field-label" htmlFor="signup-password">Password</label>
          <input
            id="signup-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            // The backend enforces this too - this only saves a round trip.
            minLength={8}
            className="field"
          />
          <p className="field-hint">At least 8 characters.</p>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" disabled={saving} className="primary wide">
            {saving ? 'Creating...' : 'Sign up'}
          </button>
        </form>

        <p className="auth-foot">
          Already have an account? <Link to="/login" className="accent-link">Log in</Link>
        </p>
      </div>
    </div>
  )
}
