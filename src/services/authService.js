import api from './api'

const authService = {
  login: (email, senha) => api.post('/auth/login', { email, senha }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  recuperarSenha: (email) => api.post('/auth/recuperar-senha', { email }),
  redefinirSenha: (token, novaSenha, confirmarSenha) =>
    api.post('/auth/redefinir-senha', { token, nova_senha: novaSenha, confirmar_senha: confirmarSenha }),
}
export default authService
