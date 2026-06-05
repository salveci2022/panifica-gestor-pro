import api from './api'

const producaoService = {
  listar:        (params = {}) => api.get('/producao', { params }),
  hoje:          ()            => api.get('/producao/hoje'),
  criar:         (dados)       => api.post('/producao', dados),
  obter:         (id)          => api.get(`/producao/${id}`),
  deletar:       (id)          => api.delete(`/producao/${id}`),
  categorias:    ()            => api.get('/producao/categorias'),
  resumoPeriodo: (params = {}) => api.get('/producao/resumo/periodo', { params }),
}
export default producaoService
