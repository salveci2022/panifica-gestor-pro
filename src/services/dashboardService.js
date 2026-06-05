import api from './api'

const dashboardService = {
  resumo: () => api.get('/dashboard/resumo'),
  fluxoCaixa: (dias = 7) => api.get(`/dashboard/fluxo-caixa?dias=${dias}`),
  alertas: () => api.get('/dashboard/alertas'),
}
export default dashboardService
