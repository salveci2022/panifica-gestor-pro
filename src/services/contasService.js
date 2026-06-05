import api from './api'

/**
 * [FIX F3] Adicionado endpoint de resumo que retorna totais em uma única
 * requisição, eliminando N+3 queries da página de contas a pagar.
 */
const contasService = {
  listar:         (params = {}) => api.get('/contas', { params }),
  criar:          (dados)       => api.post('/contas', dados),
  obter:          (id)          => api.get(`/contas/${id}`),
  atualizar:      (id, dados)   => api.put(`/contas/${id}`, dados),
  pagar:          (id, dados = {}) => api.patch(`/contas/${id}/pagar`, dados),
  cancelar:       (id)          => api.patch(`/contas/${id}/cancelar`),
  deletar:        (id)          => api.delete(`/contas/${id}`),
  historico:      (params = {}) => api.get('/contas/historico', { params }),
  categorias:     ()            => api.get('/contas/categorias'),
  criarFaturamento:   (dados)   => api.post('/contas/faturamento', dados),
  listarFaturamentos: (params = {}) => api.get('/contas/faturamento', { params }),
  atualizarFaturamento: (id, dados) => api.put(`/contas/faturamento/${id}`, dados),
  deletarFaturamento: (id)      => api.delete(`/contas/faturamento/${id}`),
  relatorioFluxo: (params = {}) => api.get('/contas/fluxo-caixa/relatorio', { params }),
}

export default contasService
