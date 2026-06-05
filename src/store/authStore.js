import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Decodifica o payload de um JWT sem verificar assinatura.
 * Usado apenas para checar expiração no lado do cliente.
 */
function decodificarJwtPayload(token) {
  try {
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return decoded
  } catch {
    return null
  }
}

/**
 * Retorna true se o token está expirado ou inválido.
 * Adiciona margem de 60s para renovar antes do vencimento real.
 */
function tokenExpirado(token) {
  if (!token) return true
  const payload = decodificarJwtPayload(token)
  if (!payload?.exp) return true
  const agora = Math.floor(Date.now() / 1000)
  return payload.exp < agora + 60  // margem de 60 segundos
}

const useAuthStore = create(
  persist(
    (set, get) => ({
      usuario: null,
      tenant: null,
      accessToken: null,
      refreshToken: null,

      setAuth: ({ usuario, tenant, access_token, refresh_token }) =>
        set({ usuario, tenant, accessToken: access_token, refreshToken: refresh_token }),

      setTokens: ({ accessToken, refreshToken }) =>
        set({ accessToken, refreshToken }),

      logout: () =>
        set({ usuario: null, tenant: null, accessToken: null, refreshToken: null }),

      // [FIX BUG-007] Verifica token válido E não expirado
      estaAutenticado: () => {
        const state = get()
        if (!state.accessToken || !state.usuario) return false
        if (tokenExpirado(state.accessToken)) return false
        return true
      },

      // Checa se precisa de refresh (token próximo de expirar)
      precisaRefresh: () => {
        const state = get()
        if (!state.accessToken) return false
        return tokenExpirado(state.accessToken)
      },

      ehProprietario: () => get().usuario?.perfil === 'proprietario',
    }),
    {
      name: 'panifica-auth',
      partialize: (s) => ({
        usuario: s.usuario,
        tenant: s.tenant,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
      }),
    }
  )
)

export default useAuthStore
