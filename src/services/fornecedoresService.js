import api from './api'

const fornecedoresService = {
  listar: (params = {}) => api.get('/fornecedores', { params }),
  criar: (dados) => api.post('/fornecedores', dados),
  obter: (id) => api.get(`/fornecedores/${id}`),
  atualizar: (id, dados) => api.put(`/fornecedores/${id}`, dados),
  deletar: (id) => api.delete(`/fornecedores/${id}`),
  categorias: () => api.get('/fornecedores/categorias'),
}
export default fornecedoresService
