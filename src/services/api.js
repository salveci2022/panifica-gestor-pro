import axios from 'axios'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, (err) => Promise.reject(err))

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    if (status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const base = import.meta.env.VITE_API_URL || '/api'
          const resp = await axios.post(`${base}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          })
          const novoToken = resp.data?.data?.access_token
          if (novoToken) {
            useAuthStore.getState().setTokens({ accessToken: novoToken, refreshToken })
            original.headers.Authorization = `Bearer ${novoToken}`
            return api(original)
          }
        } catch { /* fallthrough */ }
      }
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(error)
    }
    if (status === 403) toast.error('Sem permissão para esta ação.')
    if (status === 429) toast.error('Muitas requisições. Aguarde.')
    if (status >= 500) toast.error('Erro interno. Tente novamente.')
    return Promise.reject(error)
  }
)

export default api
