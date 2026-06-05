import { format, parseISO, isValid } from 'date-fns'
import { ptBR } from 'date-fns/locale'

export const formatBRL = (valor) => {
  const num = parseFloat(valor) || 0
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export const formatData = (data, fmt = 'dd/MM/yyyy') => {
  if (!data) return '—'
  try {
    const d = typeof data === 'string' ? parseISO(data) : data
    return isValid(d) ? format(d, fmt, { locale: ptBR }) : '—'
  } catch { return '—' }
}

export const formatDataHora = (data) => formatData(data, "dd/MM/yyyy 'às' HH:mm")

export const formatPorcentagem = (valor, casas = 1) =>
  `${(parseFloat(valor) || 0).toFixed(casas)}%`

export const statusConta = {
  pendente: { label: 'Pendente', cls: 'badge-amber' },
  paga:     { label: 'Paga',     cls: 'badge-green' },
  vencida:  { label: 'Vencida',  cls: 'badge-red' },
  cancelada:{ label: 'Cancelada',cls: 'badge-gray' },
}

export const categoriasLabel = {
  aluguel:        'Aluguel',
  energia:        'Energia',
  agua:           'Água',
  telefone:       'Telefone',
  internet:       'Internet',
  folha_pagamento:'Folha de Pagamento',
  fornecedor:     'Fornecedor',
  imposto:        'Imposto',
  manutencao:     'Manutenção',
  outro:          'Outro',
}

export const categoriasFornecedor = {
  insumos:       'Insumos',
  laticinios:    'Laticínios',
  embalagem:     'Embalagens',
  servicos:      'Serviços',
  concessionaria:'Concessionária',
  manutencao:    'Manutenção',
  outro:         'Outro',
}
