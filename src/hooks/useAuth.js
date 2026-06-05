import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'
import authService from '../services/authService'

/**
 * [FIX F2] useAuth deve ser chamado dentro de componentes que estão
 * dentro do BrowserRouter. O hook useNavigate já valida isso internamente.
 */
export function useAuth() {
  const navigate = useNavigate()
  const { setAuth, logout: logoutStore, usuario, tenant, estaAutenticado, ehProprietario } = useAuthStore()

  const login = useCallback(async (email, senha) => {
    const resp = await authService.login(email, senha)
    const { usuario, tenant, access_token, refresh_token } = resp.data.data
    setAuth({ usuario, tenant, access_token, refresh_token })
    const primeiroNome = usuario.nome?.split(' ')[0] || 'Usuário'
    toast.success(`Bem-vindo, ${primeiroNome}!`)
    navigate('/dashboard', { replace: true })
  }, [setAuth, navigate])

  const logout = useCallback(async () => {
    try { await authService.logout() } catch { /* silencioso — token pode já estar expirado */ }
    logoutStore()
    navigate('/login', { replace: true })
  }, [logoutStore, navigate])

  return {
    login,
    logout,
    usuario,
    tenant,
    estaAutenticado,
    ehProprietario,
  }
}
