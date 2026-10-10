import { defineStore } from 'pinia'
import type { CurrentUser } from '../api/generated'
import { V1Service } from '../api/generated'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: CurrentUser | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: localStorage.getItem('grindbuddy.access_token'),
    refreshToken: localStorage.getItem('grindbuddy.refresh_token'),
    user: null,
  }),
  actions: {
    setTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      localStorage.setItem('grindbuddy.access_token', accessToken)
      localStorage.setItem('grindbuddy.refresh_token', refreshToken)
    },
    async login(username: string, password: string) {
      const response = await V1Service.v1AuthTokenCreate({ username, password })
      this.setTokens(response.data.access, response.data.refresh)
      await this.fetchUser()
    },
    async fetchUser() {
      if (!this.accessToken) return
      const response = await V1Service.v1AuthMeRetrieve()
      this.user = response.data
    },
    clearTokens() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem('grindbuddy.access_token')
      localStorage.removeItem('grindbuddy.refresh_token')
    },
  },
})