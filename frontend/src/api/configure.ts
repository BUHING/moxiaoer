import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { OpenAPI } from './generated'

const ACCESS_TOKEN_KEY = 'grindbuddy.access_token'
const REFRESH_TOKEN_KEY = 'grindbuddy.refresh_token'
const TOKEN_PATH = '/api/v1/auth/token/'
const REFRESH_PATH = '/api/v1/auth/token/refresh/'

type RetryableRequestConfig = InternalAxiosRequestConfig & { _grindbuddyRetried?: boolean }

let refreshPromise: Promise<string> | null = null

function configuredBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/api\/v1\/?$/, '')
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refresh) throw new Error('No refresh token is available.')

  const response = await axios.post<{ data: { access: string } }>(
    `${OpenAPI.BASE}${REFRESH_PATH}`,
    { refresh },
  )
  localStorage.setItem(ACCESS_TOKEN_KEY, response.data.data.access)
  return response.data.data.access
}

export function configureApi() {
  OpenAPI.BASE = configuredBaseUrl()
  OpenAPI.TOKEN = async () => localStorage.getItem(ACCESS_TOKEN_KEY) ?? ''

  axios.interceptors.response.use(undefined, async (error: AxiosError) => {
    const request = error.config as RetryableRequestConfig | undefined
    const url = request?.url ?? ''
    if (
      error.response?.status !== 401
      || !request
      || request._grindbuddyRetried
      || url.endsWith(TOKEN_PATH)
      || url.endsWith(REFRESH_PATH)
    ) {
      return Promise.reject(error)
    }

    request._grindbuddyRetried = true
    refreshPromise ??= refreshAccessToken().finally(() => { refreshPromise = null })

    try {
      const accessToken = await refreshPromise
      request.headers.set('Authorization', `Bearer ${accessToken}`)
      return axios.request(request)
    } catch (refreshError) {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      if (window.location.pathname !== '/auth') window.location.assign('/auth')
      return Promise.reject(refreshError)
    }
  })
}