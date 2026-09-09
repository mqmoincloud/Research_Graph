import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import { changePassword, updateMyName } from '../api/auth'

export default function Profile() {
  // Handed down by Layout, which got it from /me.
  const user = useOutletContext()

  const [name, setName] = useState(user.name)
  const [nameMsg, setNameMsg] = useState('')
  const [nameError, setNameError] = useState('')
  const [savingName, setSavingName] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordMsg, setPasswordMsg] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [savingPassword, setSavingPassword] = useState(false)

  async function handleName(e) {
    e.preventDefault()
    if (savingName) return

    const cleanName = name.trim()

    if (!cleanName) {
      setNameError('Name is required.')
      return
    }

    setNameMsg('')
    setNameError('')
    setSavingName(true)

    try {
      await updateMyName(cleanName)
      setNameMsg('Saved.')
      // The top bar is showing the OLD name until Layout asks /me again.
      user.reloadUser()
    } catch (err) {
      setNameError(err.message)
    } finally {
      setSavingName(false)
    }
  }

  async function handlePassword(e) {
    e.preventDefault()
    if (savingPassword) return

    if (!currentPassword.trim()) {
      setPasswordError('Current password is required.')
      return
    }

    if (!newPassword.trim()) {
      setPasswordError('New password cannot be blank or only spaces.')
      return
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters.')
      return
    }

    setPasswordMsg('')
    setPasswordError('')
    setSavingPassword(true)

    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      // The backend bumped token_version, so the token in this tab is dead.
      // The very next request will 401 and drop us on /login - saying so is
      // better than letting it look like a bug.
      setPasswordMsg('Password changed. You will be asked to log in again.')
    } catch (err) {
      setPasswordError(err.message)
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Profile</h1>
        <p>{user.email} &middot; {user.role}</p>
      </header>

      <form onSubmit={handleName} className="card">
        <div className="card-head"><h3>Name</h3></div>

        <label className="field-label" htmlFor="profile-name">Display name</label>
        <input
          id="profile-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="field"
        />

        {/* Email is deliberately not editable here. It is the login
            identifier, and changing it by mistake locks you out - an admin
            can do it from the Users page if it is really needed. */}

        {nameError && <p className="error-text">{nameError}</p>}
        {nameMsg && <p className="ok-text">{nameMsg}</p>}

        <button type="submit" disabled={savingName} className="primary">
          {savingName ? 'Saving...' : 'Save name'}
        </button>
      </form>

      <form onSubmit={handlePassword} className="card stacked">
        <div className="card-head"><h3>Password</h3></div>

        <label className="field-label" htmlFor="profile-current">Current password</label>
        <input
          id="profile-current"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
          className="field"
        />

        <label className="field-label" htmlFor="profile-new">New password</label>
        <input
          id="profile-new"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={8}
          className="field"
        />
        <p className="field-hint">At least 8 characters.</p>

        {passwordError && <p className="error-text">{passwordError}</p>}
        {passwordMsg && <p className="ok-text">{passwordMsg}</p>}

        <button type="submit" disabled={savingPassword} className="primary">
          {savingPassword ? 'Saving...' : 'Change password'}
        </button>
      </form>
    </div>
  )
}
