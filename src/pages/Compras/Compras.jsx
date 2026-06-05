import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import comprasService from '../../services/comprasService'
import estoqueService from '../../services/estoqueService'
import fornecedoresService from '../../services/fornecedoresService'
import { formatBRL, formatData } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'

const UNIDADES = ['kg','g','l','ml','un','cx','sc','dz','pct']
const FORMAS   = ['pix','boleto','cartao_debito','cartao_credito','dinheiro','transferencia','cheque']

const ITEM_VAZIO = { descricao:'', unidade:'kg', quantidade:'', valor_unitario:'', item_estoque_id:'' }

function NovaCompraModal({ aberto, onFechar, onSalvo, fornecedores, itensEstoque }) {
  const [form, setForm] = useState({
    data_compra: new Date().toISOString().split('T')[0],
    fornecedor_id: '',
    numero_nota: '',
    forma_pagamento: '',
    status_pagamento: 'pendente',
    observacoes: '',
  })
  const [itens, setItens]   = useState([{ ...ITEM_VAZIO }])
  const [salvando, setSalv] = useState(false)

  useEffect(() => {
    if (aberto) {
      setForm({ data_compra: new Date().toISOString().split('T')[0], fornecedor_id:'', numero_nota:'', forma_pagamento:'', status_pagamento:'pendente', observacoes:'' })
      setItens([{ ...ITEM_VAZIO }])
    }
  }, [aberto])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setItem = (idx, k, v) => setItens(its => its.map((it, i) => i === idx ? { ...it, [k]: v } : it))
  const addItem = () => setItens(its => [...its, { ...ITEM_VAZIO }])
  const remItem = (idx) => setItens(its => its.filter((_, i) => i !== idx))

  const totalCompra = itens.reduce((acc, it) => {
    const q = parseFloat(it.quantidade) || 0
    const v = parseFloat(it.valor_unitario) || 0
    return acc + q * v
  }, 0)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.data_compra) return toast.error('Informe a data.')
    if (itens.some(it => !it.descricao.trim())) return toast.error('Preencha a descrição de todos os itens.')
    if (itens.some(it => !it.quantidade || parseFloat(it.quantidade) <= 0)) return toast.error('Quantidade inválida em algum item.')
    if (itens.some(it => !it.valor_unitario || parseFloat(it.valor_unitario) <= 0)) return toast.error('Valor unitário inválido em algum item.')

    setSalv(true)
    try {
      const payload = {
        ...form,
        fornecedor_id:   form.fornecedor_id || null,
        forma_pagamento: form.forma_pagamento || null,
        itens: itens.map(it => ({
          descricao:       it.descricao.trim(),
          unidade:         it.unidade,
          quantidade:      parseFloat(it.quantidade),
          valor_unitario:  parseFloat(it.valor_unitario),
          item_estoque_id: it.item_estoque_id || null,
        }))
      }
      await comprasService.criar(payload)
      toast.success('Compra registrada! Estoque atualizado automaticamente.')
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao registrar compra.')
    } finally { setSalv(false) }
  }

  return (
    <Modal aberto={aberto} onFechar={onFechar} titulo="Registrar nova compra" largura="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Data da compra *</label>
            <input type="date" className="input-base" value={form.data_compra}
              onChange={e => setF('data_compra', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Fornecedor</label>
            <select className="input-base" value={form.fornecedor_id} onChange={e => setF('fornecedor_id', e.target.value)}>
              <option value="">— Nenhum —</option>
              {(fornecedores || []).map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
            </select>
          </div>
          <div>
            <label className="label-base">Nº da nota fiscal</label>
            <input className="input-base" placeholder="NF 001234"
              value={form.numero_nota} onChange={e => setF('numero_nota', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Forma de pagamento</label>
            <select className="input-base" value={form.forma_pagamento} onChange={e => setF('forma_pagamento', e.target.value)}>
              <option value="">— Selecione —</option>
              {FORMAS.map(f => <option key={f} value={f}>{f.replace(/_/g,' ')}</option>)}
            </select>
          </div>
        </div>

        {/* Itens da compra */}
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-slate-700">Itens da compra</p>
            <button type="button" className="btn-ghost text-xs py-1" onClick={addItem}>+ Adicionar item</button>
          </div>
          <div className="space-y-2">
            {itens.map((it, idx) => (
              <div key={idx} className="grid gap-2 items-end" style={{ gridTemplateColumns: '2fr 1fr 1fr 1fr 2fr auto' }}>
                <div>
                  {idx === 0 && <div className="text-[10px] text-slate-400 mb-1">Descrição *</div>}
                  <input className="input-base text-xs py-1.5" placeholder="Farinha de trigo"
                    value={it.descricao} onChange={e => setItem(idx,'descricao',e.target.value)} />
                </div>
                <div>
                  {idx === 0 && <div className="text-[10px] text-slate-400 mb-1">Unidade</div>}
                  <select className="input-base text-xs py-1.5" value={it.unidade} onChange={e => setItem(idx,'unidade',e.target.value)}>
                    {UNIDADES.map(u => <option key={u} value={u}>{u}</option>)}
                  </select>
                </div>
                <div>
                  {idx === 0 && <div className="text-[10px] text-slate-400 mb-1">Quantidade</div>}
                  <input type="number" min="0.001" step="0.001" className="input-base text-xs py-1.5" placeholder="0"
                    value={it.quantidade} onChange={e => setItem(idx,'quantidade',e.target.value)} />
                </div>
                <div>
                  {idx === 0 && <div className="text-[10px] text-slate-400 mb-1">Vl. unitário</div>}
                  <input type="number" min="0.0001" step="0.0001" className="input-base text-xs py-1.5" placeholder="0,00"
                    value={it.valor_unitario} onChange={e => setItem(idx,'valor_unitario',e.target.value)} />
                </div>
                <div>
                  {idx === 0 && <div className="text-[10px] text-slate-400 mb-1">Vincular ao estoque</div>}
                  <select className="input-base text-xs py-1.5" value={it.item_estoque_id} onChange={e => setItem(idx,'item_estoque_id',e.target.value)}>
                    <option value="">— Não vincular —</option>
                    {(itensEstoque || []).map(ie => <option key={ie.id} value={ie.id}>{ie.nome} ({ie.unidade})</option>)}
                  </select>
                </div>
                <div>
                  {idx === 0 && <div className="text-[10px] text-transparent mb-1">x</div>}
                  <button type="button" onClick={() => remItem(idx)} disabled={itens.length === 1}
                    className="p-1.5 text-rose-400 hover:text-rose-600 disabled:opacity-30 transition-colors">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M18 6L6 18M6 6l12 12"/></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-200">
            <span className="text-sm text-slate-500">Total da compra:</span>
            <span className="text-base font-semibold text-blue-700">{formatBRL(totalCompra)}</span>
          </div>
        </div>

        <div>
          <label className="label-base">Observações</label>
          <input className="input-base" placeholder="Notas adicionais..."
            value={form.observacoes} onChange={e => setF('observacoes', e.target.value)} />
        </div>

        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1" onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center" disabled={salvando}>
            {salvando ? <><Spinner size="sm" className="border-white/30 border-t-white"/>Registrando…</> : 'Registrar compra'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function Compras() {
  const [dados, setDados]         = useState({ data: [], meta: {} })
  const [carregando, setLoad]     = useState(true)
  const [modalAberto, setModal]   = useState(false)
  const [confirmCancel, setConf]  = useState(null)
  const [processando, setProc]    = useState(false)
  const [fornecedores, setForn]   = useState([])
  const [itensEstoque, setItensE] = useState([])
  const [resumoMes, setResumoMes] = useState(null)

  const carregar = useCallback(async () => {
    setLoad(true)
    try {
      const [r, rm] = await Promise.all([
        comprasService.listar(),
        comprasService.resumoMes(),
      ])
      setDados(r.data)
      setResumoMes(rm.data.data)
    } catch { toast.error('Erro ao carregar compras.') }
    finally { setLoad(false) }
  }, [])

  useEffect(() => {
    carregar()
    Promise.all([
      fornecedoresService.listar(),
      estoqueService.listar(),
    ]).then(([rf, re]) => {
      setForn(rf.data.data || [])
      setItensE(re.data.itens || [])
    }).catch(() => {})
  }, [carregar])

  const cancelarCompra = async () => {
    setProc(true)
    try {
      await comprasService.cancelar(confirmCancel.id)
      toast.success('Compra cancelada e estoque estornado.')
      setConf(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao cancelar.')
    } finally { setProc(false) }
  }

  const compras = dados.data || []

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Registro de Compras</h1>
          <p className="text-sm text-slate-500 mt-0.5">Compras atualizadas automaticamente no estoque</p>
        </div>
        <button className="btn-primary" onClick={() => setModal(true)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><path d="M12 5v14M5 12h14"/></svg>
          Nova compra
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="kpi-card">
          <p className="kpi-label">Total de compras (mês)</p>
          <p className="kpi-value">{formatBRL(resumoMes?.total_mes || 0)}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Qtd. de compras</p>
          <p className="kpi-value">{dados.meta?.total || 0}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Ticket médio</p>
          <p className="kpi-value">
            {formatBRL(dados.meta?.total > 0 ? (resumoMes?.total_mes || 0) / dados.meta.total : 0)}
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
        {carregando ? <PageLoader /> : compras.length === 0 ? (
          <EmptyState
            icone={<svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>}
            titulo="Nenhuma compra registrada"
            descricao="Registre a primeira compra para atualizar o estoque automaticamente."
            acao={<button className="btn-primary" onClick={() => setModal(true)}>Registrar compra</button>}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 text-slate-300">
                  {['Data','Fornecedor','Itens','Valor total','Pagamento','Status','Ações'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {compras.map(compra => (
                  <tr key={compra.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-4 py-3 text-slate-600">{formatData(compra.data_compra)}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800">{compra.fornecedor_nome || '—'}</div>
                      {compra.numero_nota && <div className="text-[10px] text-slate-400">{compra.numero_nota}</div>}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{(compra.itens || []).length} item(ns)</td>
                    <td className="px-4 py-3 font-semibold text-slate-800">{formatBRL(compra.valor_total)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs capitalize">{compra.forma_pagamento?.replace(/_/g,' ') || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`badge text-xs font-medium px-2 py-0.5 rounded-full ${
                        compra.status_pagamento === 'pago'
                          ? 'bg-emerald-50 text-emerald-700'
                          : compra.status_pagamento === 'cancelado'
                          ? 'bg-slate-100 text-slate-500'
                          : 'bg-amber-50 text-amber-700'
                      }`}>
                        {compra.status_pagamento}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {compra.status_pagamento !== 'cancelado' && (
                        <button onClick={() => setConf(compra)}
                          className="btn-ghost text-xs py-1 px-2 text-rose-400 hover:text-rose-600">
                          Cancelar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <NovaCompraModal aberto={modalAberto} onFechar={() => setModal(false)}
        onSalvo={carregar} fornecedores={fornecedores} itensEstoque={itensEstoque} />
      <Confirm aberto={!!confirmCancel} onFechar={() => setConf(null)}
        onConfirmar={cancelarCompra} titulo="Cancelar compra"
        mensagem={`Cancelar compra de ${formatBRL(confirmCancel?.valor_total || 0)}? O estoque será estornado automaticamente.`}
        carregando={processando} />
    </div>
  )
}
