import { useState, useCallback, useEffect } from 'react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import toast from 'react-hot-toast'
import contasService from '../../services/contasService'
import useAuthStore from '../../store/authStore'
import dashboardService from '../../services/dashboardService'
import { formatBRL, formatData, formatPorcentagem } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { PageLoader, Spinner } from '../../components/ui/Spinner'

const TooltipCustom = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs shadow-2xl min-w-[160px]">
      <p className="text-slate-300 font-medium mb-2">{label}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex justify-between gap-4 mb-1">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="text-white font-medium">{formatBRL(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

// [FIX F6] Anos dinâmicos — ano atual e 2 anteriores
function gerarAnos() {
  const ano = new Date().getFullYear()
  return [ano - 2, ano - 1, ano]
}

const MESES = [
  'Jan','Fev','Mar','Abr','Mai','Jun',
  'Jul','Ago','Set','Out','Nov','Dez'
]

export default function FluxoCaixa() {
  const hoje = new Date()
  const [fluxo,    setFluxo]    = useState(null)
  const [relatorio, setRel]     = useState(null)
  const [carregando, setLoad]   = useState(true)
  const [dias, setDias]         = useState(14)
  const [periodo, setPeriodo]   = useState({
    ano: hoje.getFullYear(),
    mes: hoje.getMonth() + 1,
  })
  const [modalFat, setModalFat]     = useState(false)
  const [formFat, setFormFat]       = useState({ data: '', valor: '', descricao: '' })
  const [salvando, setSalvando]     = useState(false)

  const ANOS = gerarAnos()

  const carregar = useCallback(async () => {
    setLoad(true)
    try {
      const [f, r] = await Promise.all([
        dashboardService.fluxoCaixa(dias),
        contasService.relatorioFluxo({ ano: periodo.ano, mes: periodo.mes }),
      ])
      setFluxo(f.data.data)
      setRel(r.data.data)
    } catch {
      toast.error('Erro ao carregar fluxo de caixa.')
    } finally {
      setLoad(false)
    }
  }, [dias, periodo])

  useEffect(() => { carregar() }, [carregar])

  const salvarFat = async (e) => {
    e.preventDefault()
    if (!formFat.data) return toast.error('Informe a data.')
    if (!formFat.valor || parseFloat(formFat.valor) <= 0)
      return toast.error('Valor inválido.')

    setSalvando(true)
    try {
      await contasService.criarFaturamento({
        data:      formFat.data,
        valor:     parseFloat(formFat.valor),
        descricao: formFat.descricao.trim() || null,
      })
      toast.success('Receita registrada!')
      setModalFat(false)
      setFormFat({ data: '', valor: '', descricao: '' })
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao registrar.')
    } finally {
      setSalvando(false)
    }
  }

  const dadosGrafico = (fluxo?.fluxo || []).map(d => ({
    data:      formatData(d.data, 'dd/MM'),
    Entradas:  parseFloat(d.entradas)  || 0,
    'Saídas':  parseFloat(d.saidas)    || 0,
    'Saldo': parseFloat(d.saldo_acumulado) || 0,
  }))

  const token = useAuthStore(s => s.accessToken)

  const baixarPDF = async () => {
    try {
      const resp = await fetch(
        `http://localhost:5000/api/relatorios/financeiro/pdf?ano=${periodo.ano}&mes=${periodo.mes}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!resp.ok) { alert('Erro ao gerar PDF'); return }
      const blob = await resp.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `relatorio_${periodo.ano}_${String(periodo.mes).padStart(2,'0')}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch { alert('Erro ao baixar PDF.') }
  }

  if (carregando && !fluxo) return <PageLoader />

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Fluxo de Caixa</h1>
          <p className="text-sm text-slate-500 mt-0.5">Entradas, saídas e saldo por período</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {/* [FIX F6] Seletor de período dinâmico */}
          <select className="input-base w-auto text-xs py-1.5" value={periodo.mes}
            onChange={e => setPeriodo(p => ({ ...p, mes: parseInt(e.target.value) }))}>
            {MESES.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
          </select>
          <select className="input-base w-auto text-xs py-1.5" value={periodo.ano}
            onChange={e => setPeriodo(p => ({ ...p, ano: parseInt(e.target.value) }))}>
            {ANOS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <button onClick={baixarPDF} className="btn-secondary text-xs py-1.5 px-3">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Baixar PDF
          </button>
          <button onClick={() => setModalFat(true)} className="btn-primary text-xs py-1.5 px-3">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth={2.5}><path d="M12 5v14M5 12h14"/></svg>
            Lançar receita
          </button>
        </div>
      </div>

      {/* KPIs do mês */}
      {relatorio && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="kpi-card">
            <p className="kpi-label">Entradas do mês</p>
            <p className="kpi-value text-emerald-600">{formatBRL(relatorio.faturamento_total)}</p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Saídas do mês</p>
            <p className="kpi-value text-rose-600">{formatBRL(relatorio.despesas_total)}</p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Saldo / Lucro</p>
            <p className={`kpi-value ${relatorio.lucro_estimado >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {formatBRL(relatorio.lucro_estimado)}
            </p>
          </div>
          <div className="kpi-card">
            <p className="kpi-label">Margem líquida</p>
            <p className={`kpi-value ${relatorio.margem_percentual >= 10 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {formatPorcentagem(relatorio.margem_percentual)}
            </p>
          </div>
        </div>
      )}

      {/* Gráfico */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">Entradas vs Saídas</h3>
            <p className="text-xs text-slate-400 mt-0.5">Comparativo diário com saldo acumulado</p>
          </div>
          <div className="flex gap-1">
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setDias(d)}
                className={`px-2.5 py-1 text-xs rounded-lg transition-colors ${
                  dias === d ? 'bg-blue-600 text-white' : 'text-slate-500 hover:bg-slate-100'
                }`}>{d}d</button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={dadosGrafico} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
            <XAxis dataKey="data" tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false} tickLine={false}/>
            <YAxis yAxisId="bars" tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false} tickLine={false}
              tickFormatter={v => `R$${(v/1000).toFixed(0)}k`}/>
            <YAxis yAxisId="linha" orientation="right"
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false} tickLine={false}
              tickFormatter={v => `R$${(v/1000).toFixed(0)}k`}/>
            <Tooltip content={<TooltipCustom />}/>
            <ReferenceLine yAxisId="bars" y={0} stroke="#e2e8f0"/>
            <Bar yAxisId="bars" dataKey="Entradas" fill="#3b82f6"
              radius={[3,3,0,0]} maxBarSize={28}/>
            <Bar yAxisId="bars" dataKey="Saídas" fill="#f43f5e"
              radius={[3,3,0,0]} maxBarSize={28}/>
            <Line yAxisId="linha" type="monotone" dataKey="Saldo"
              stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="4 2"/>
          </ComposedChart>
        </ResponsiveContainer>
        <div className="flex gap-5 mt-3 justify-center flex-wrap">
          {[
            { cor: 'bg-blue-500', label: 'Entradas' },
            { cor: 'bg-rose-500', label: 'Saídas' },
            { cor: 'bg-amber-400', label: 'Saldo acumulado' },
          ].map(({ cor, label }) => (
            <span key={label} className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className={`w-2 h-2 rounded-full ${cor}`}/>
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Despesas por categoria */}
      {relatorio?.saidas_por_categoria?.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">Saídas por categoria</h3>
          <div className="space-y-3">
            {relatorio.saidas_por_categoria
              .sort((a, b) => b.total - a.total)
              .map(({ categoria, total }) => {
                const pct = relatorio.despesas_total > 0
                  ? Math.round((total / relatorio.despesas_total) * 100) : 0
                return (
                  <div key={categoria}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-600 capitalize">
                        {categoria.replace(/_/g, ' ')}
                      </span>
                      <span className="font-medium text-slate-800">
                        {formatBRL(total)}{' '}
                        <span className="text-slate-400">({pct}%)</span>
                      </span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}/>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      )}

      {/* Modal lançar receita */}
      <Modal aberto={modalFat} onFechar={() => setModalFat(false)}
        titulo="Lançar receita" largura="max-w-sm">
        <form onSubmit={salvarFat} className="space-y-4">
          <div>
            <label className="label-base">Data *</label>
            <input type="date" className="input-base" value={formFat.data}
              onChange={e => setFormFat(f => ({ ...f, data: e.target.value }))} />
          </div>
          <div>
            <label className="label-base">Valor (R$) *</label>
            <input type="number" min="0.01" step="0.01" className="input-base"
              placeholder="0,00" value={formFat.valor}
              onChange={e => setFormFat(f => ({ ...f, valor: e.target.value }))} />
          </div>
          <div>
            <label className="label-base">Descrição (opcional)</label>
            <input className="input-base"
              placeholder="Faturamento do dia, vendas balcão…"
              value={formFat.descricao}
              onChange={e => setFormFat(f => ({ ...f, descricao: e.target.value }))} />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" className="btn-secondary flex-1"
              onClick={() => setModalFat(false)} disabled={salvando}>Cancelar</button>
            <button type="submit" className="btn-primary flex-1 justify-center"
              disabled={salvando}>
              {salvando
                ? <><Spinner size="sm" className="border-white/30 border-t-white"/>Salvando…</>
                : 'Registrar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
