
import api, { saveToken } from './client'

export async function signup(name, email, password) {
  const res = await api.post('/auth/signup', { name, email, password })
  return res.data
}

export async function login(email, password) {
  const res = await api.post('/auth/login', { email, password })
  saveToken(res.data.access_token)
  return res.data
}

export async function getMe() {
  const res = await api.get('/me')
  return res.data
}

export async function updateMyName(name) {
  const res = await api.patch('/me', { name })
  return res.data
}

export async function changePassword(currentPassword, newPassword) {
  const res = await api.post('/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return res.data
}

export async function getUsers() {
  const res = await api.get('/admin/users')
  return res.data
}

export async function updateUser(id, changes) {
  const res = await api.patch(`/users/${id}`, changes)
  return res.data
}

export async function deleteUser(id) {
  const res = await api.delete(`/users/${id}`)
  return res.data
}
