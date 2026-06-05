import api from './api'

const notificacoesService = {
  status:            ()           => api.get('/notificacoes/status'),
  alertaVencimentos: (numero)     => api.post('/notificacoes/alerta-vencimentos', { numero }),
  alertaEstoque:     (numero)     => api.post('/notificacoes/alerta-estoque', { numero }),
  resumoDiario:      (numero)     => api.post('/notificacoes/resumo-diario', { numero }),
}
export default notificacoesService
