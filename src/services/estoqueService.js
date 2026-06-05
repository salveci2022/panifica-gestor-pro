import api from './api'

const estoqueService = {
  listar:       (params = {}) => api.get('/estoque', { params }),
  criar:        (dados)       => api.post('/estoque', dados),
  obter:        (id)          => api.get(`/estoque/${id}`),
  atualizar:    (id, dados)   => api.put(`/estoque/${id}`, dados),
  desativar:    (id)          => api.delete(`/estoque/${id}`),
  ajuste:       (id, dados)   => api.post(`/estoque/${id}/ajuste`, dados),
  alertas:      ()            => api.get('/estoque/alertas'),
  unidades:     ()            => api.get('/estoque/unidades'),
}
export default estoqueService
