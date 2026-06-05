import api from './api'

const comprasService = {
  listar:      (params = {}) => api.get('/compras', { params }),
  criar:       (dados)       => api.post('/compras', dados),
  obter:       (id)          => api.get(`/compras/${id}`),
  cancelar:    (id)          => api.delete(`/compras/${id}`),
  resumoMes:   ()            => api.get('/compras/resumo/mes'),
}
export default comprasService
