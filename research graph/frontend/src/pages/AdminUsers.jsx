import { useCallback, useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import { deleteUser, getUsers, updateUser } from '../api/auth'

// The admin screen. Two things can be done to somebody else: change their
// role, or remove them.
//
// Both buttons are hidden on your own row, because the API refuses both with a
// 409 - an admin demoting or deleting themselves could leave the app with no
// admin at all and no way back in. Hiding them here just saves the round trip;
// the real rule is in app/routers/auth.py.
export default function AdminUsers() {
  const me = useOutletContext()

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  // Which row is mid-request, so only that row's buttons go dead.
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setError('')
    try {
      setUsers(await getUsers())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleRole(user) {
    setBusyId(user.id)
    setError('')
    try {
      await updateUser(user.id, { role: user.role === 'admin' ? 'user' : 'admin' })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(user) {
    if (!confirm(`Remove ${user.name}? They will not be able to log in.`)) return

    setBusyId(user.id)
    setError('')
    try {
      await deleteUser(user.id)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <p className="page">Loading...</p>

  return (
    <div className="page">
      <header className="header">
        <h1>Users</h1>
        <p>Everyone who can log in. Admins only.</p>
      </header>

      {error && <div className="error-box">{error}</div>}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>
                  {user.name}
                  {user.id === me.id && <span className="tag">you</span>}
                </td>
                <td className="dim">{user.email}</td>
                <td>{user.role}</td>
                <td className="row-actions">
                  {user.id !== me.id && (
                    <>
                      <button
                        className="link"
                        disabled={busyId === user.id}
                        onClick={() => handleRole(user)}
                      >
                        {user.role === 'admin' ? 'Make user' : 'Make admin'}
                      </button>
                      <button
                        className="link danger"
                        disabled={busyId === user.id}
                        onClick={() => handleDelete(user)}
                      >
                        Remove
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
