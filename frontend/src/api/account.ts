import axios from 'axios'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')

export async function requestPasswordReset(email: string) {
  await axios.post(`${apiBaseUrl}/auth/password-reset/`, { email })
}

export async function confirmPasswordReset(uid: string, token: string, password: string) {
  await axios.post(`${apiBaseUrl}/auth/password-reset/confirm/`, { uid, token, password })
}

export async function deleteDocument(path: string) {
  await axios.delete(`${apiBaseUrl}${path}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('grindbuddy.access_token') ?? ''}` },
  })
}