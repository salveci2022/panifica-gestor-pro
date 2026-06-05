import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import estoqueService from '../../services/estoqueService'
import { formatBRL, formatData } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'
import { Badge } from '../../components/ui/Badge'

const UNIDADES = ['kg','g','l','ml','un','cx','sc','dz','pct']

const FORM_VAZIO = { nome:'', unidade:'kg', quantidade_atual:'0', quantidade_minima:'0', custo_medio:'' }
const AJUSTE_VAZIO = { tipo:'entrada', quantidade:'', custo_unitario:'', motivo:'' }

function ModalItem({ aberto, onFechar, onSalvo, item }) {
  const [form, setForm] = useState(FORM_VAZIO)
  const [salvando, setSalvando] = useState(false)
  const editando = !!item

  useEffect(() => {
    if (aberto) setForm(item ? {
      nome:              item.nome || '',
      unidade:           item.unidade || 'kg',
      quantidade_atual:  String(item.quantidade_atual ?? 0),
      quantidade_minima: String(item.quantidade_minima ?? 0),
      custo_medio:       item.custo_medio ? String(item.custo_medio) : '',
    } : FORM_VAZIO)
  }, [aberto, item])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.nome.trim()) return toast.error('Informe o nome do item.')
    setSalvando(true)
    try {
      const payload = {
        nome:              form.nome.trim(),
        unidade:           form.unidade,
        quantidade_minima: parseFloat(form.quantidade_minima) || 0,
        ...(editando ? {} : { quantidade_atual: parseFloat(form.quantidade_atual) || 0 }),
        ...(form.custo_medio ? { custo_medio: parseFloat(form.custo_medio) } : {}),
      }
      if (editando) {
        await estoqueService.atualizar(item.id, payload)
        toast.success('Item atualizado.')
      } else {
        await estoqueService.criar(payload)
        toast.success('Item cadastrado.')
      }
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao salvar.')
    } finally { setSalvando(false) }
  }

  return (
    <Modal aberto={aberto} onFechar={onFechar}
      titulo={editando ? 'Editar item' : 'Novo item de estoque'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label-base">Nome do item *</label>
          <input className="input-base" placeholder="Ex: Farinha de trigo tipo 1"
            value={form.nome} onChange={e => set('nome', e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Unidade *</label>
            <select className="input-base" value={form.unidade} onChange={e => set('unidade', e.target.value)}>
              {UNIDADES.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <div>
            <label className="label-base">Qtd. mínima (alerta)</label>
            <input type="number" min="0" step="0.001" className="input-base"
              value={form.quantidade_minima} onChange={e => set('quantidade_minima', e.target.value)} />
          </div>
        </div>
        {!editando && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-base">Qtd. inicial em estoque</label>
              <input type="number" min="0" step="0.001" className="input-base"
                value={form.quantidade_atual} onChange={e => set('quantidade_atual', e.target.value)} />
            </div>
            <div>
              <label className="label-base">Custo médio unitário (R$)</label>
              <input type="number" min="0" step="0.0001" className="input-base"
                placeholder="0,00" value={form.custo_medio} onChange={e => set('custo_medio', e.target.value)} />
            </div>
          </div>
        )}
        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1" onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center" disabled={salvando}>
            {salvando ? <><Spinner size="sm" className="border-white/30 border-t-white" />Salvando…</> : (editando ? 'Salvar' : 'Cadastrar')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function ModalAjuste({ aberto, onFechar, onSalvo, item }) {
  const [form, setForm] = useState(AJUSTE_VAZIO)
  const [salvando, setSalvando] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => { if (aberto) setForm(AJUSTE_VAZIO) }, [aberto])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.quantidade || parseFloat(form.quantidade) <= 0) return toast.error('Quantidade inválida.')
    if ((form.tipo === 'ajuste' || form.tipo === 'perda') && !form.motivo.trim())
      return toast.error('Informe o motivo para ajuste ou perda.')

    setSalvando(true)
    try {
      const payload = {
        tipo:      form.tipo,
        quantidade: parseFloat(form.quantidade),
        ...(form.motivo.trim() ? { motivo: form.motivo.trim() } : {}),
        ...(form.custo_unitario ? { custo_unitario: parseFloat(form.custo_unitario) } : {}),
      }
      await estoqueService.ajuste(item.id, payload)
      toast.success('Ajuste registrado.')
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao registrar ajuste.')
    } finally { setSalvando(false) }
  }

  const TIPOS = [
    { valor: 'entrada', label: '+ Entrada' },
    { valor: 'saida',   label: '− Saída' },
    { valor: 'ajuste',  label: '⟳ Ajuste (definir valor)' },
    { valor: 'perda',   label: '✕ Perda / Descarte' },
  ]

  return (
    <Modal aberto={aberto} onFechar={onFechar}
      titulo={`Movimentação — ${item?.nome || ''}`} largura="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-slate-50 rounded-lg p-3 text-sm">
          <span className="text-slate-500">Saldo atual: </span>
          <span className="font-semibold text-slate-800">
            {item?.quantidade_atual} {item?.unidade}
          </span>
        </div>
        <div>
          <label className="label-base">Tipo *</label>
          <select className="input-base" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
            {TIPOS.map(t => <option key={t.valor} value={t.valor}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label-base">Quantidade ({item?.unidade}) *</label>
          <input type="number" min="0.001" step="0.001" className="input-base"
            placeholder="0,000" value={form.quantidade} onChange={e => set('quantidade', e.target.value)} />
        </div>
        {form.tipo === 'entrada' && (
          <div>
            <label className="label-base">Custo unitário (R$) — opcional</label>
            <input type="number" min="0" step="0.0001" className="input-base"
              placeholder="0,0000" value={form.custo_unitario} onChange={e => set('custo_unitario', e.target.value)} />
          </div>
        )}
        {(form.tipo === 'ajuste' || form.tipo === 'perda') && (
          <div>
            <label className="label-base">Motivo *</label>
            <input className="input-base" placeholder="Descreva o motivo..."
              value={form.motivo} onChange={e => set('motivo', e.target.value)} />
          </div>
        )}
        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1" onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center" disabled={salvando}>
            {salvando ? <><Spinner size="sm" className="border-white/30 border-t-white" />Salvando…</> : 'Registrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function Estoque() {
  const [dados, setDados]         = useState({ itens: [], total: 0, total_alertas: 0 })
  const [carregando, setLoad]     = useState(true)
  const [busca, setBusca]         = useState('')
  const [apenasAlerta, setAlerta] = useState(false)
  const [modalItem, setModalItem] = useState(false)
  const [modalAjuste, setModalAjuste] = useState(false)
  const [itemSelecionado, setItemSel] = useState(null)
  const [confirmDesativ, setConfDesativ] = useState(null)
  const [processando, setProc]    = useState(false)

  const carregar = useCallback(async () => {
    setLoad(true)
    try {
      const params = {}
      if (busca) params.busca = busca
      if (apenasAlerta) params.alerta = true
      const r = await estoqueService.listar(params)
      setDados(r.data.data)
    } catch { toast.error('Erro ao carregar estoque.') }
    finally { setLoad(false) }
  }, [busca, apenasAlerta])

  useEffect(() => { carregar() }, [carregar])

  const desativar = async () => {
    setProc(true)
    try {
      await estoqueService.desativar(confirmDesativ.id)
      toast.success('Item desativado.')
      setConfDesativ(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao desativar.')
    } finally { setProc(false) }
  }

  const itens = dados.itens || []

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Controle de Estoque</h1>
          <p className="text-sm text-slate-500 mt-0.5">{dados.total} item(ns) · {dados.total_alertas} em alerta</p>
        </div>
        <button className="btn-primary" onClick={() => { setItemSel(null); setModalItem(true) }}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><path d="M12 5v14M5 12h14"/></svg>
          Novo item
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <div className="kpi-card">
          <p className="kpi-label">Total de itens</p>
          <p className="kpi-value">{dados.total}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label text-rose-600">Em alerta</p>
          <p className="kpi-value text-rose-600">{dados.total_alertas}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Itens normais</p>
          <p className="kpi-value text-emerald-600">{dados.total - dados.total_alertas}</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[180px]">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input className="input-base pl-8" placeholder="Buscar item..."
            value={busca} onChange={e => setBusca(e.target.value)} />
        </div>
        <button
          onClick={() => setAlerta(v => !v)}
          className={`px-3.5 py-2 text-xs font-medium rounded-lg border transition-all ${
            apenasAlerta ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}>
          {apenasAlerta ? '✕ Limpar filtro' : '⚠ Ver apenas alertas'}
        </button>
      </div>

      {/* Tabela */}
      <div className="card overflow-hidden">
        {carregando ? <PageLoader /> : itens.length === 0 ? (
          <EmptyState
            icone={<svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2z"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>}
            titulo="Nenhum item encontrado"
            descricao="Cadastre os insumos da padaria para controlar o estoque."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 text-slate-300">
                  {['Item','Unidade','Qtd. atual','Qtd. mínima','Status','Custo médio','Ações'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {itens.map(item => (
                  <tr key={item.id}
                    className={`hover:bg-slate-50/60 transition-colors ${item.em_alerta ? 'bg-rose-50/30' : ''}`}>
                    <td className="px-4 py-3">
                      <div className={`font-medium text-sm ${item.em_alerta ? 'text-rose-700' : 'text-slate-800'}`}>
                        {item.em_alerta && '⚠ '}{item.nome}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{item.unidade}</td>
                    <td className="px-4 py-3">
                      <span className={`font-semibold ${item.em_alerta ? 'text-rose-600' : 'text-slate-800'}`}>
                        {item.quantidade_atual}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{item.quantidade_minima}</td>
                    <td className="px-4 py-3">
                      <span className={`badge text-xs font-medium px-2 py-0.5 rounded-full ${
                        item.em_alerta ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'
                      }`}>
                        {item.em_alerta ? 'Crítico' : 'Normal'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {item.custo_medio ? formatBRL(item.custo_medio) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 justify-end">
                        <button onClick={() => { setItemSel(item); setModalAjuste(true) }}
                          className="btn-success text-xs py-1 px-2.5">
                          Movimentar
                        </button>
                        <button onClick={() => { setItemSel(item); setModalItem(true) }}
                          className="btn-ghost text-xs py-1 px-2">
                          Editar
                        </button>
                        <button onClick={() => setConfDesativ(item)}
                          className="btn-ghost text-xs py-1 px-2 text-rose-400 hover:text-rose-600">
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ModalItem aberto={modalItem} onFechar={() => setModalItem(false)}
        onSalvo={carregar} item={itemSelecionado} />
      <ModalAjuste aberto={modalAjuste} onFechar={() => setModalAjuste(false)}
        onSalvo={carregar} item={itemSelecionado} />
      <Confirm aberto={!!confirmDesativ} onFechar={() => setConfDesativ(null)}
        onConfirmar={desativar} titulo="Desativar item"
        mensagem={`Desativar "${confirmDesativ?.nome}"? O item não aparecerá mais no estoque.`}
        carregando={processando} />
    </div>
  )
}
