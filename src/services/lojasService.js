import api from './api'

const lojasService = {
  listar:       ()             => api.get('/lojas'),
  criar:        (dados)        => api.post('/lojas', dados),
  obter:        (id)           => api.get(`/lojas/${id}`),
  atualizar:    (id, dados)    => api.put(`/lojas/${id}`, dados),
  desativar:    (id)           => api.delete(`/lojas/${id}`),
  resumoContas: ()             => api.get('/lojas/resumo/contas'),
}
export default lojasService
