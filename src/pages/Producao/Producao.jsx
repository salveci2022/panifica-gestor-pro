import { useState, useEffect, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import toast from 'react-hot-toast'
import producaoService from '../../services/producaoService'
import { formatBRL, formatData } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'

const CATEGORIAS = ['paes','bolos','salgados','doces','bebidas','outro']
const UNIDADES   = ['un','kg','bandeja','dz','pct']
const CAT_CORES  = { paes:'#3b82f6', bolos:'#f59e0b', salgados:'#10b981', doces:'#f43f5e', bebidas:'#8b5cf6', outro:'#94a3b8' }
const CAT_LABELS = { paes:'Pães', bolos:'Bolos', salgados:'Salgados', doces:'Doces', bebidas:'Bebidas', outro:'Outros' }

const FORM_VAZIO = {
  data_producao: new Date().toISOString().split('T')[0],
  produto: '', categoria: 'paes', quantidade: '', unidade: 'un',
  custo_estimado: '', observacoes: ''
}

function ModalProducao({ aberto, onFechar, onSalvo }) {
  const [form, setForm]   = useState(FORM_VAZIO)
  const [salvando, setSalv]= useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => { if (aberto) setForm(FORM_VAZIO) }, [aberto])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.produto.trim()) return toast.error('Informe o produto.')
    if (!form.quantidade || parseFloat(form.quantidade) <= 0) return toast.error('Quantidade inválida.')
    setSalv(true)
    try {
      await producaoService.criar({
        data_producao:  form.data_producao,
        produto:        form.produto.trim(),
        categoria:      form.categoria,
        quantidade:     parseFloat(form.quantidade),
        unidade:        form.unidade,
        custo_estimado: form.custo_estimado ? parseFloat(form.custo_estimado) : null,
        observacoes:    form.observacoes || null,
      })
      toast.success('Produção registrada.')
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao registrar.')
    } finally { setSalv(false) }
  }

  return (
    <Modal aberto={aberto} onFechar={onFechar} titulo="Registrar produção" largura="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label-base">Data *</label>
          <input type="date" className="input-base" value={form.data_producao}
            onChange={e => set('data_producao', e.target.value)} />
        </div>
        <div>
          <label className="label-base">Produto *</label>
          <input className="input-base" placeholder="Ex: Pão francês, Bolo de cenoura..."
            value={form.produto} onChange={e => set('produto', e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Categoria *</label>
            <select className="input-base" value={form.categoria} onChange={e => set('categoria', e.target.value)}>
              {CATEGORIAS.map(c => <option key={c} value={c}>{CAT_LABELS[c]}</option>)}
            </select>
          </div>
          <div>
            <label className="label-base">Unidade *</label>
            <select className="input-base" value={form.unidade} onChange={e => set('unidade', e.target.value)}>
              {UNIDADES.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-base">Quantidade *</label>
            <input type="number" min="0.01" step="0.01" className="input-base"
              placeholder="0" value={form.quantidade} onChange={e => set('quantidade', e.target.value)} />
          </div>
          <div>
            <label className="label-base">Custo estimado (R$)</label>
            <input type="number" min="0" step="0.01" className="input-base"
              placeholder="0,00" value={form.custo_estimado} onChange={e => set('custo_estimado', e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label-base">Observações</label>
          <input className="input-base" placeholder="Notas do turno..."
            value={form.observacoes} onChange={e => set('observacoes', e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1" onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center" disabled={salvando}>
            {salvando ? <><Spinner size="sm" className="border-white/30 border-t-white"/>Salvando…</> : 'Registrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

const TooltipCustom = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 rounded-lg p-3 text-xs shadow-xl border border-slate-700">
      <p className="text-slate-300 mb-1.5 font-medium">{label}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex justify-between gap-4 mb-1">
          <span style={{ color: p.fill }}>{p.dataKey}</span>
          <span className="text-white font-medium">{p.value} {p.payload.unidade}</span>
        </div>
      ))}
    </div>
  )
}

export default function Producao() {
  const [hoje, setHoje]           = useState({ itens: [], total: 0 })
  const [resumo, setResumo]       = useState([])
  const [carregando, setLoad]     = useState(true)
  const [modalAberto, setModal]   = useState(false)
  const [confirmDel, setConfDel]  = useState(null)
  const [processando, setProc]    = useState(false)

  const carregar = useCallback(async () => {
    setLoad(true)
    try {
      const [rh, rr] = await Promise.all([
        producaoService.hoje(),
        producaoService.resumoPeriodo(),
      ])
      setHoje(rh.data.data)
      setResumo(rr.data.data?.resumo || [])
    } catch { toast.error('Erro ao carregar produção.') }
    finally { setLoad(false) }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  const deletar = async () => {
    setProc(true)
    try {
      await producaoService.deletar(confirmDel.id)
      toast.success('Registro removido.')
      setConfDel(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao remover.')
    } finally { setProc(false) }
  }

  // Agrupar hoje por categoria para o gráfico
  const dadosGrafico = Object.entries(
    (hoje.itens || []).reduce((acc, it) => {
      const cat = CAT_LABELS[it.categoria] || it.categoria
      acc[cat] = (acc[cat] || 0) + parseFloat(it.quantidade)
      return acc
    }, {})
  ).map(([cat, qtd]) => ({ categoria: cat, Quantidade: qtd }))

  const totalCusto = (hoje.itens || []).reduce((acc, it) => acc + parseFloat(it.custo_estimado || 0), 0)

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Produção Diária</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {new Date().toLocaleDateString('pt-BR', { weekday:'long', day:'numeric', month:'long' })}
          </p>
        </div>
        <button className="btn-primary" onClick={() => setModal(true)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><path d="M12 5v14M5 12h14"/></svg>
          Registrar produção
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <div className="kpi-card">
          <p className="kpi-label">Registros hoje</p>
          <p className="kpi-value">{hoje.total}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Categorias produzidas</p>
          <p className="kpi-value">{new Set((hoje.itens||[]).map(i=>i.categoria)).size}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Custo estimado hoje</p>
          <p className="kpi-value">{formatBRL(totalCusto)}</p>
        </div>
      </div>

      {/* Gráfico + Tabela hoje */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {dadosGrafico.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-800 mb-4">Produção por categoria — hoje</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={dadosGrafico} margin={{ top:0, right:0, bottom:0, left:0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                <XAxis dataKey="categoria" tick={{ fontSize:10, fill:'#94a3b8' }} axisLine={false} tickLine={false}/>
                <YAxis tick={{ fontSize:10, fill:'#94a3b8' }} axisLine={false} tickLine={false}/>
                <Tooltip content={<TooltipCustom />}/>
                <Bar dataKey="Quantidade" fill="#3b82f6" radius={[3,3,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className={`card overflow-hidden ${dadosGrafico.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-800">Registros de hoje</h3>
          </div>
          {carregando ? <PageLoader /> : (hoje.itens||[]).length === 0 ? (
            <EmptyState
              icone={<svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M18 8h1a4 4 0 010 8h-1"/><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>}
              titulo="Nenhuma produção registrada hoje"
              acao={<button className="btn-primary" onClick={() => setModal(true)}>Registrar agora</button>}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-900 text-slate-300">
                    {['Produto','Categoria','Quantidade','Custo est.','Ações'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(hoje.itens||[]).map(it => (
                    <tr key={it.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-800">{it.produto}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full"
                          style={{ background: `${CAT_CORES[it.categoria]}20`, color: CAT_CORES[it.categoria] }}>
                          {CAT_LABELS[it.categoria] || it.categoria}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-700">{it.quantidade} {it.unidade}</td>
                      <td className="px-4 py-3 text-slate-500">
                        {it.custo_estimado ? formatBRL(it.custo_estimado) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => setConfDel(it)}
                          className="btn-ghost text-xs py-1 px-2 text-rose-400 hover:text-rose-600">
                          Remover
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Resumo da semana */}
      {resumo.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">Resumo dos últimos 7 dias — por produto</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 text-slate-300">
                  {['Produto','Categoria','Total produzido','Custo total'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {resumo.map((r, i) => (
                  <tr key={i} className={`hover:bg-slate-50/60 ${i % 2 === 0 ? '' : 'bg-slate-50/30'}`}>
                    <td className="px-4 py-3 font-medium text-slate-800">{r.produto}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{ background:`${CAT_CORES[r.categoria]}20`, color:CAT_CORES[r.categoria] }}>
                        {CAT_LABELS[r.categoria] || r.categoria}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-700">{r.total_quantidade} {r.unidade}</td>
                    <td className="px-4 py-3 text-slate-500">{r.total_custo > 0 ? formatBRL(r.total_custo) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ModalProducao aberto={modalAberto} onFechar={() => setModal(false)} onSalvo={carregar} />
      <Confirm aberto={!!confirmDel} onFechar={() => setConfDel(null)}
        onConfirmar={deletar} titulo="Remover registro"
        mensagem={`Remover "${confirmDel?.produto} — ${confirmDel?.quantidade} ${confirmDel?.unidade}"?`}
        carregando={processando} />
    </div>
  )
}
