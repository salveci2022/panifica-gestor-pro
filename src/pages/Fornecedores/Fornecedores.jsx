import { useState, useCallback, useEffect } from 'react'
import toast from 'react-hot-toast'
import fornecedoresService from '../../services/fornecedoresService'
import { categoriasFornecedor, formatData } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'

const CATEGORIAS = ['insumos','laticinios','embalagem','servicos','concessionaria','manutencao','outro']

const formVazio = {
  nome: '', cnpj_cpf: '', categoria: 'outro', telefone: '',
  whatsapp: '', email: '', contato_nome: '', endereco: '', observacoes: ''
}

const COR_CATEGORIA = {
  insumos:       'bg-blue-100 text-blue-700',
  laticinios:    'bg-emerald-100 text-emerald-700',
  embalagem:     'bg-amber-100 text-amber-700',
  servicos:      'bg-purple-100 text-purple-700',
  concessionaria:'bg-rose-100 text-rose-700',
  manutencao:    'bg-orange-100 text-orange-700',
  outro:         'bg-slate-100 text-slate-600',
}

function Inicial({ nome }) {
  const letras = nome?.split(' ').slice(0, 2).map(p => p[0]?.toUpperCase()).join('') || '?'
  const cores = ['bg-blue-200 text-blue-800','bg-emerald-200 text-emerald-800','bg-amber-200 text-amber-800','bg-purple-200 text-purple-800','bg-rose-200 text-rose-800']
  const cor = cores[letras.charCodeAt(0) % cores.length]
  return (
    <div className={`w-10 h-10 rounded-full ${cor} flex items-center justify-center text-sm font-semibold flex-shrink-0`}>
      {letras}
    </div>
  )
}

function ModalFornecedor({ aberto, onFechar, onSalvo, fornecedor }) {
  const [form, setForm] = useState(formVazio)
  const [salvando, setSalvando] = useState(false)
  const editando = !!fornecedor

  useEffect(() => {
    if (aberto) {
      setForm(fornecedor ? {
        nome: fornecedor.nome || '',
        cnpj_cpf: fornecedor.cnpj_cpf || '',
        categoria: fornecedor.categoria || 'outro',
        telefone: fornecedor.telefone || '',
        whatsapp: fornecedor.whatsapp || '',
        email: fornecedor.email || '',
        contato_nome: fornecedor.contato_nome || '',
        endereco: fornecedor.endereco || '',
        observacoes: fornecedor.observacoes || '',
      } : formVazio)
    }
  }, [aberto, fornecedor])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.nome.trim()) return toast.error('Informe o nome do fornecedor.')
    setSalvando(true)
    try {
      const payload = { ...form }
      Object.keys(payload).forEach(k => { if (payload[k] === '') payload[k] = null })
      payload.nome = form.nome
      payload.categoria = form.categoria

      if (editando) {
        await fornecedoresService.atualizar(fornecedor.id, payload)
        toast.success('Fornecedor atualizado.')
      } else {
        await fornecedoresService.criar(payload)
        toast.success('Fornecedor cadastrado.')
      }
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao salvar.')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal aberto={aberto} onFechar={onFechar}
      titulo={editando ? 'Editar fornecedor' : 'Novo fornecedor'}
      largura="max-w-xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label-base">Nome / Razão social *</label>
            <input className="input-base" placeholder="Distribuidora Farinha Norte"
              value={form.nome} onChange={e => set('nome', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Categoria *</label>
            <select className="input-base" value={form.categoria} onChange={e => set('categoria', e.target.value)}>
              {CATEGORIAS.map(c => <option key={c} value={c}>{categoriasFornecedor[c]}</option>)}
            </select>
          </div>
          <div>
            <label className="label-base">CNPJ / CPF</label>
            <input className="input-base" placeholder="00.000.000/0001-00"
              value={form.cnpj_cpf} onChange={e => set('cnpj_cpf', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Telefone</label>
            <input className="input-base" placeholder="(61) 3000-0000"
              value={form.telefone} onChange={e => set('telefone', e.target.value)} />
          </div>
          <div>
            <label className="label-base">WhatsApp</label>
            <input className="input-base" placeholder="(61) 99900-0000"
              value={form.whatsapp} onChange={e => set('whatsapp', e.target.value)} />
          </div>
          <div className="col-span-2">
            <label className="label-base">E-mail</label>
            <input type="email" className="input-base" placeholder="contato@fornecedor.com.br"
              value={form.email} onChange={e => set('email', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Nome do contato</label>
            <input className="input-base" placeholder="Fulano Silva"
              value={form.contato_nome} onChange={e => set('contato_nome', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Endereço</label>
            <input className="input-base" placeholder="Rua, número, cidade"
              value={form.endereco} onChange={e => set('endereco', e.target.value)} />
          </div>
          <div className="col-span-2">
            <label className="label-base">Observações</label>
            <textarea className="input-base resize-none" rows={2}
              placeholder="Prazo de entrega, condições especiais…"
              value={form.observacoes} onChange={e => set('observacoes', e.target.value)} />
          </div>
        </div>
        <div className="flex gap-3 pt-1">
          <button type="button" className="btn-secondary flex-1" onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center" disabled={salvando}>
            {salvando ? <><Spinner size="sm" className="border-white/30 border-t-white" /> Salvando…</> : (editando ? 'Salvar' : 'Cadastrar')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function Fornecedores() {
  const [lista, setLista] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [busca, setBusca] = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [modalAberto, setModalAberto] = useState(false)
  const [fornecedorEditando, setFornecedorEditando] = useState(null)
  const [confirmDesativar, setConfirmDesativar] = useState(null)
  const [processando, setProcessando] = useState(false)

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      const params = {}
      if (busca) params.busca = busca
      if (categoriaFiltro) params.categoria = categoriaFiltro
      const resp = await fornecedoresService.listar(params)
      setLista(resp.data.data || [])
    } catch {
      toast.error('Erro ao carregar fornecedores.')
    } finally {
      setCarregando(false)
    }
  }, [busca, categoriaFiltro])

  useEffect(() => { carregar() }, [carregar])

  const desativar = async () => {
    setProcessando(true)
    try {
      await fornecedoresService.deletar(confirmDesativar.id)
      toast.success('Fornecedor desativado.')
      setConfirmDesativar(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao desativar.')
    } finally {
      setProcessando(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Fornecedores</h1>
          <p className="text-sm text-slate-500 mt-0.5">{lista.length} fornecedor(es) cadastrado(s)</p>
        </div>
        <button className="btn-primary" onClick={() => { setFornecedorEditando(null); setModalAberto(true) }}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Novo fornecedor
        </button>
      </div>

      {/* Busca e filtros */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[180px]">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input className="input-base pl-8" placeholder="Buscar por nome…"
            value={busca} onChange={e => setBusca(e.target.value)} />
        </div>
        <select className="input-base w-auto min-w-[140px]" value={categoriaFiltro}
          onChange={e => setCategoriaFiltro(e.target.value)}>
          <option value="">Todas as categorias</option>
          {CATEGORIAS.map(c => <option key={c} value={c}>{categoriasFornecedor[c]}</option>)}
        </select>
      </div>

      {/* Cards */}
      {carregando ? (
        <PageLoader />
      ) : lista.length === 0 ? (
        <EmptyState
          icone={<svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>}
          titulo="Nenhum fornecedor encontrado"
          descricao="Cadastre seus fornecedores para vincular às compras e contas."
          acao={<button className="btn-primary" onClick={() => setModalAberto(true)}>Cadastrar primeiro fornecedor</button>}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {lista.map(forn => (
            <div key={forn.id} className="card p-4 hover:shadow-md transition-shadow group">
              <div className="flex items-start gap-3 mb-3">
                <Inicial nome={forn.nome} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-800 truncate">{forn.nome}</p>
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${COR_CATEGORIA[forn.categoria] || COR_CATEGORIA.outro}`}>
                    {categoriasFornecedor[forn.categoria] || forn.categoria}
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 text-xs text-slate-500">
                {forn.telefone && (
                  <div className="flex items-center gap-1.5">
                    <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.77a19.79 19.79 0 01-3.07-8.67A2 2 0 012 .84h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 8.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
                    </svg>
                    {forn.telefone}
                  </div>
                )}
                {forn.whatsapp && (
                  <div className="flex items-center gap-1.5">
                    <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.77a19.79 19.79 0 01-3.07-8.67A2 2 0 012 .84h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 8.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
                    </svg>
                    {forn.whatsapp} <span className="text-green-600">(WA)</span>
                  </div>
                )}
                {forn.email && (
                  <div className="flex items-center gap-1.5 truncate">
                    <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                      <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <span className="truncate">{forn.email}</span>
                  </div>
                )}
                {forn.cnpj_cpf && (
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <path d="M9 9h6M9 13h6M9 17h4"/>
                    </svg>
                    {forn.cnpj_cpf}
                  </div>
                )}
              </div>

              <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
                <button
                  onClick={() => { setFornecedorEditando(forn); setModalAberto(true) }}
                  className="btn-ghost text-xs flex-1 justify-center py-1.5">
                  Editar
                </button>
                <button
                  onClick={() => setConfirmDesativar(forn)}
                  className="btn-ghost text-xs flex-1 justify-center py-1.5 text-rose-400 hover:text-rose-600 hover:bg-rose-50">
                  Desativar
                </button>
              </div>
            </div>
          ))}

          {/* Card para adicionar */}
          <button
            onClick={() => { setFornecedorEditando(null); setModalAberto(true) }}
            className="card p-4 border-dashed hover:border-blue-300 hover:bg-blue-50/30 flex flex-col items-center justify-center gap-2 text-slate-400 hover:text-blue-500 transition-all min-h-[160px]">
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path d="M12 5v14M5 12h14"/>
            </svg>
            <span className="text-xs">Adicionar fornecedor</span>
          </button>
        </div>
      )}

      {/* Modais */}
      <ModalFornecedor
        aberto={modalAberto}
        onFechar={() => setModalAberto(false)}
        onSalvo={carregar}
        fornecedor={fornecedorEditando}
      />

      <Confirm
        aberto={!!confirmDesativar}
        onFechar={() => setConfirmDesativar(null)}
        onConfirmar={desativar}
        titulo="Desativar fornecedor"
        mensagem={`Deseja desativar "${confirmDesativar?.nome}"? O fornecedor não aparecerá mais nas listagens.`}
        carregando={processando}
      />
    </div>
  )
}
