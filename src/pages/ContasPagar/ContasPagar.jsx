import { useState, useCallback, useEffect } from 'react'
import toast from 'react-hot-toast'
import contasService from '../../services/contasService'
import fornecedoresService from '../../services/fornecedoresService'
import lojasService from '../../services/lojasService'
import { formatBRL, formatData, categoriasLabel } from '../../utils/formatters'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'

const FILTROS = [
  { valor: '',         label: 'Todas' },
  { valor: 'pendente', label: 'Pendentes' },
  { valor: 'vencida',  label: 'Vencidas' },
  { valor: 'paga',     label: 'Pagas' },
]

const CATEGORIAS = [
  'aluguel','energia','agua','telefone','internet',
  'folha_pagamento','fornecedor','imposto','manutencao','outro'
]
const FORMAS = [
  'pix','boleto','cartao_debito','cartao_credito','dinheiro','transferencia','cheque'
]

const FORM_VAZIO = {
  descricao: '', categoria: 'outro', valor: '', vencimento: '',
  forma_pagamento: '', fornecedor_id: '', loja_id: '', numero_pedido: '', observacoes: ''
}

// ─── Modal de criar / editar ──────────────────────────────────────────────────
function ModalConta({ aberto, onFechar, onSalvo, conta, fornecedores, lojas }) {
  const [form, setForm] = useState(FORM_VAZIO)
  const [salvando, setSalvando] = useState(false)
  const editando = !!conta

  useEffect(() => {
    if (aberto) setForm(conta ? {
      descricao:       conta.descricao || '',
      categoria:       conta.categoria || 'outro',
      valor:           conta.valor || '',
      vencimento:      conta.vencimento || '',
      forma_pagamento: conta.forma_pagamento || '',
      fornecedor_id:   conta.fornecedor_id || '',
      observacoes:     conta.observacoes || '',
      loja_id:         conta.loja_id || '',
      numero_pedido:   conta.numero_pedido || '',
    } : FORM_VAZIO)
  }, [aberto, conta])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.descricao.trim()) return toast.error('Informe a descrição.')
    if (!form.valor || parseFloat(form.valor) <= 0) return toast.error('Valor inválido.')
    if (!form.vencimento) return toast.error('Informe o vencimento.')

    setSalvando(true)
    try {
      const payload = {
        descricao:       form.descricao.trim(),
        categoria:       form.categoria,
        valor:           parseFloat(form.valor),
        vencimento:      form.vencimento,
        forma_pagamento: form.forma_pagamento || null,
        fornecedor_id:   form.fornecedor_id || null,
        observacoes:     form.observacoes.trim() || null,
        loja_id:         form.loja_id || null,
        numero_pedido:   form.numero_pedido.trim() || null,
      }
      if (editando) {
        await contasService.atualizar(conta.id, payload)
        toast.success('Conta atualizada.')
      } else {
        await contasService.criar(payload)
        toast.success('Conta cadastrada.')
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
      titulo={editando ? 'Editar conta' : 'Nova conta a pagar'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label-base">Descrição *</label>
          <input className="input-base" placeholder="Ex: Aluguel de junho"
            value={form.descricao} onChange={e => set('descricao', e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Categoria *</label>
            <select className="input-base" value={form.categoria}
              onChange={e => set('categoria', e.target.value)}>
              {CATEGORIAS.map(c => (
                <option key={c} value={c}>{categoriasLabel[c] || c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-base">Valor (R$) *</label>
            <input type="number" min="0.01" step="0.01" className="input-base"
              placeholder="0,00" value={form.valor}
              onChange={e => set('valor', e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Vencimento *</label>
            <input type="date" className="input-base" value={form.vencimento}
              onChange={e => set('vencimento', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Forma de pagamento</label>
            <select className="input-base" value={form.forma_pagamento}
              onChange={e => set('forma_pagamento', e.target.value)}>
              <option value="">— Selecione —</option>
              {FORMAS.map(f => (
                <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="label-base">Fornecedor (opcional)</label>
          <select className="input-base" value={form.fornecedor_id}
            onChange={e => set('fornecedor_id', e.target.value)}>
            <option value="">— Nenhum —</option>
            {(fornecedores || []).map(f => (
              <option key={f.id} value={f.id}>{f.nome}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Loja / Unidade</label>
            <select className="input-base" value={form.loja_id}
              onChange={e => set('loja_id', e.target.value)}>
              <option value="">— Todas as lojas —</option>
              {(lojas || []).map(l => (
                <option key={l.id} value={l.id}>{l.codigo ? l.codigo + ' — ' : ''}{l.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-base">Nº do pedido</label>
            <input className="input-base" placeholder="Ex: PED-001"
              value={form.numero_pedido}
              onChange={e => set('numero_pedido', e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label-base">Observações</label>
          <textarea className="input-base resize-none" rows={2}
            placeholder="Notas adicionais…" value={form.observacoes}
            onChange={e => set('observacoes', e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1"
            onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center"
            disabled={salvando}>
            {salvando
              ? <><Spinner size="sm" className="border-white/30 border-t-white" />Salvando…</>
              : editando ? 'Salvar' : 'Cadastrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────────
export default function ContasPagar() {
  const [contas, setContas]         = useState([])
  const [meta, setMeta]             = useState({})
  const [carregando, setCarregando] = useState(true)
  const [statusFiltro, setStatus]   = useState('')
  const [pagina, setPagina]         = useState(1)
  const [modalAberto, setModal]     = useState(false)
  const [contaEdit, setContaEdit]   = useState(null)
  const [confirmPagar, setConfPagar]= useState(null)
  const [confirmCancel, setConfCancel]= useState(null)
  const [processando, setProc]      = useState(false)
  const [fornecedores, setForn]     = useState([])
  const [lojas, setLojas]           = useState([])

  // [FIX F3] Totais buscados em UMA única requisição junto com a listagem
  const [totais, setTotais] = useState({ pendente: 0, vencida: 0, paga: 0 })

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      const params = { pagina, por_pagina: 15 }
      if (statusFiltro) params.status = statusFiltro

      // [FIX F3] Uma requisição para lista + três paralelas para contadores
      const [rLista, rPend, rVenc, rPaga] = await Promise.all([
        contasService.listar(params),
        contasService.listar({ status: 'pendente', por_pagina: 1, pagina: 1 }),
        contasService.listar({ status: 'vencida',  por_pagina: 1, pagina: 1 }),
        contasService.listar({ status: 'paga',     por_pagina: 1, pagina: 1 }),
      ])
      setContas(rLista.data.data || [])
      setMeta(rLista.data.meta || {})
      setTotais({
        pendente: rPend.data.meta?.total || 0,
        vencida:  rVenc.data.meta?.total || 0,
        paga:     rPaga.data.meta?.total || 0,
      })
    } catch {
      toast.error('Erro ao carregar contas.')
    } finally {
      setCarregando(false)
    }
  }, [statusFiltro, pagina])

  useEffect(() => {
    Promise.all([
      fornecedoresService.listar(),
      lojasService.listar(),
    ]).then(([rf, rl]) => {
      setForn(rf.data.data || [])
      setLojas(rl.data.data || [])
    }).catch(() => {})
  }, [])

  useEffect(() => { carregar() }, [carregar])

  const pagarConta = async () => {
    setProc(true)
    try {
      await contasService.pagar(confirmPagar.id)
      toast.success('Conta marcada como paga!')
      setConfPagar(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao pagar.')
    } finally { setProc(false) }
  }

  const cancelarConta = async () => {
    setProc(true)
    try {
      await contasService.cancelar(confirmCancel.id)
      toast.success('Conta cancelada.')
      setConfCancel(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao cancelar.')
    } finally { setProc(false) }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Contas a Pagar</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gerencie seus compromissos financeiros</p>
        </div>
        <button className="btn-primary"
          onClick={() => { setContaEdit(null); setModal(true) }}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Nova conta
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Pendentes',    val: totais.pendente, cor: 'text-amber-600' },
          { label: 'Vencidas',     val: totais.vencida,  cor: 'text-rose-600' },
          { label: 'Pagas (mês)', val: totais.paga,     cor: 'text-emerald-600' },
        ].map(({ label, val, cor }) => (
          <div key={label} className="kpi-card">
            <p className="kpi-label">{label}</p>
            <p className={`text-xl font-semibold ${cor}`}>{val}</p>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className="flex gap-2 flex-wrap">
        {FILTROS.map(({ valor, label }) => (
          <button key={valor}
            onClick={() => { setStatus(valor); setPagina(1) }}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg border transition-all ${
              statusFiltro === valor
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}>
            {label}
            {valor === 'vencida' && totais.vencida > 0 && (
              <span className="ml-1.5 bg-rose-500 text-white text-[9px] px-1.5 py-0.5 rounded-full">
                {totais.vencida}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tabela */}
      <div className="card overflow-hidden">
        {carregando ? (
          <PageLoader />
        ) : contas.length === 0 ? (
          <EmptyState
            icone={
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth={1.5}>
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
                <rect x="9" y="3" width="6" height="4" rx="1"/>
              </svg>
            }
            titulo="Nenhuma conta encontrada"
            descricao="Cadastre sua primeira conta a pagar."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 text-slate-300">
                  {['Descrição','Categoria','Valor','Vencimento','Status','Ações'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {contas.map(conta => (
                  <tr key={conta.id}
                    className={`hover:bg-slate-50/60 transition-colors ${
                      conta.status === 'vencida' ? 'bg-rose-50/30' : ''
                    }`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800 text-sm">{conta.descricao}</div>
                      {conta.fornecedor_nome && (
                        <div className="text-[10px] text-slate-400 mt-0.5">{conta.fornecedor_nome}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {categoriasLabel[conta.categoria] || conta.categoria}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-semibold text-sm ${
                        conta.status === 'vencida' ? 'text-rose-600' : 'text-slate-800'
                      }`}>{formatBRL(conta.valor)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${
                        conta.status === 'vencida' ? 'text-rose-600 font-medium' : 'text-slate-600'
                      }`}>{formatData(conta.vencimento)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge status={conta.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 justify-end flex-wrap">
                        {(conta.status === 'pendente' || conta.status === 'vencida') && (
                          <button onClick={() => setConfPagar(conta)} className="btn-success text-xs py-1 px-2.5">
                            ✓ Pagar
                          </button>
                        )}
                        {conta.status !== 'paga' && conta.status !== 'cancelada' && (
                          <button
                            onClick={() => { setContaEdit(conta); setModal(true) }}
                            className="btn-ghost text-xs py-1 px-2">
                            Editar
                          </button>
                        )}
                        {conta.status !== 'cancelada' && conta.status !== 'paga' && (
                          <button
                            onClick={() => setConfCancel(conta)}
                            className="btn-ghost text-xs py-1 px-2 text-slate-400 hover:text-rose-500">
                            ✕
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginação */}
        {meta.total_paginas > 1 && (
          <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-400">
              {meta.total} registros · pág. {meta.pagina}/{meta.total_paginas}
            </span>
            <div className="flex gap-1.5">
              <button disabled={pagina <= 1} onClick={() => setPagina(p => p - 1)}
                className="btn-ghost text-xs py-1 px-2.5 disabled:opacity-30">← Ant.</button>
              <button disabled={pagina >= meta.total_paginas} onClick={() => setPagina(p => p + 1)}
                className="btn-ghost text-xs py-1 px-2.5 disabled:opacity-30">Próx. →</button>
            </div>
          </div>
        )}
      </div>

      {/* Modais */}
      <ModalConta aberto={modalAberto} onFechar={() => setModal(false)}
        onSalvo={carregar} conta={contaEdit} fornecedores={fornecedores} lojas={lojas} />

      <Confirm aberto={!!confirmPagar} onFechar={() => setConfPagar(null)}
        onConfirmar={pagarConta} titulo="Confirmar pagamento"
        mensagem={`Pagar ${formatBRL(confirmPagar?.valor)} — "${confirmPagar?.descricao}"?`}
        carregando={processando} />

      <Confirm aberto={!!confirmCancel} onFechar={() => setConfCancel(null)}
        onConfirmar={cancelarConta} titulo="Cancelar conta"
        mensagem={`Cancelar "${confirmCancel?.descricao}"? Não pode ser desfeito.`}
        carregando={processando} />
    </div>
  )
}
