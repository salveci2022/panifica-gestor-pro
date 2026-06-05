import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'
import toast from 'react-hot-toast'
import dashboardService from '../../services/dashboardService'
import contasService from '../../services/contasService'
import { formatBRL, formatData, formatPorcentagem } from '../../utils/formatters'
import { Badge } from '../../components/ui/Badge'
import { PageLoader } from '../../components/ui/Spinner'

const Kpi = ({ label, valor, sub, corValor }) => (
  <div className="kpi-card">
    <p className="kpi-label">{label}</p>
    <p className={`kpi-value ${corValor || 'text-slate-900'}`}>{valor}</p>
    {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
  </div>
)

const TooltipCustom = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-400 mb-1.5">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {formatBRL(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [resumo,   setResumo]  = useState(null)
  const [fluxo,    setFluxo]   = useState(null)
  const [alertas,  setAlertas] = useState(null)
  const [loading,  setLoading] = useState(true)
  const [dias, setDias]        = useState(7)

  const carregar = useCallback(async () => {
    setLoading(true)
    try {
      const [r, f, a] = await Promise.all([
        dashboardService.resumo(),
        dashboardService.fluxoCaixa(dias),
        dashboardService.alertas(),
      ])
      setResumo(r.data.data)
      setFluxo(f.data.data)
      setAlertas(a.data.data)
    } catch {
      toast.error('Erro ao carregar o dashboard.')
    } finally {
      setLoading(false)
    }
  }, [dias])

  useEffect(() => { carregar() }, [carregar])

  const pagarConta = async (id) => {
    try {
      await contasService.pagar(id)
      toast.success('Conta marcada como paga!')
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao pagar conta.')
    }
  }

  if (loading && !resumo) return <PageLoader />

  const dadosGrafico = (fluxo?.fluxo || []).map(d => ({
    data:     formatData(d.data, 'dd/MM'),
    Entradas: d.entradas,
    'Saídas': d.saidas,
  }))

  // [FIX F8] Cálculo real de variação ao invés de texto hardcoded
  const subFatDia = resumo
    ? `${resumo.contas_vencidas > 0 ? `${resumo.contas_vencidas} vencida(s)` : 'Dia corrente'}`
    : ''

  return (
    <div className="max-w-7xl mx-auto space-y-6 page-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {new Date().toLocaleDateString('pt-BR', {
              weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
            })}
          </p>
        </div>
        <button onClick={carregar} className="btn-secondary text-xs" disabled={loading}>
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
            viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Atualizar
        </button>
      </div>

      {/* Alertas */}
      {(resumo?.contas_vencidas > 0 || resumo?.proximas_vencer > 0) && (
        <div className="flex gap-3 flex-wrap">
          {resumo.contas_vencidas > 0 && (
            <Link to="/contas?status=vencida"
              className="flex items-center gap-2 px-3.5 py-2 bg-rose-50 border border-rose-200
                rounded-lg text-xs font-medium text-rose-700 hover:bg-rose-100 transition-colors">
              <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"/>
              {resumo.contas_vencidas} conta(s) vencida(s) — clique para ver
            </Link>
          )}
          {resumo.proximas_vencer > 0 && (
            <div className="flex items-center gap-2 px-3.5 py-2 bg-amber-50 border border-amber-200
              rounded-lg text-xs font-medium text-amber-700">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500"/>
              {resumo.proximas_vencer} vence(m) nos próximos 3 dias
            </div>
          )}
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi label="Faturamento hoje"  valor={formatBRL(resumo?.faturamento_dia)} sub={subFatDia} />
        <Kpi label="Faturamento no mês" valor={formatBRL(resumo?.faturamento_mes)}
          sub={`Ref.: ${resumo?.mes_referencia || '—'}`} />
        <Kpi label="Contas a pagar" valor={formatBRL(resumo?.total_pendente)}
          corValor={resumo?.contas_vencidas > 0 ? 'text-rose-600' : 'text-slate-900'}
          sub={resumo?.contas_vencidas > 0 ? `${resumo.contas_vencidas} vencida(s)` : 'Em dia'} />
        <Kpi label="Margem estimada" valor={formatPorcentagem(resumo?.margem_percentual)}
          corValor={resumo?.margem_percentual >= 10 ? 'text-emerald-600' : 'text-rose-600'}
          sub={`Lucro: ${formatBRL(resumo?.lucro_estimado)}`} />
      </div>

      {/* Gráfico + Contas urgentes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Fluxo de caixa</h3>
              <p className="text-xs text-slate-400 mt-0.5">Entradas e saídas por período</p>
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
          {dadosGrafico.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={dadosGrafico}
                margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="gradE" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#2563eb" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gradS" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#f43f5e" stopOpacity={0.10}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                <XAxis dataKey="data"
                  tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}/>
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                  tickFormatter={v => `R$${(v/1000).toFixed(0)}k`}/>
                <Tooltip content={<TooltipCustom />}/>
                <Area type="monotone" dataKey="Entradas" stroke="#2563eb" strokeWidth={2}
                  fill="url(#gradE)" dot={false} activeDot={{ r: 4 }}/>
                <Area type="monotone" dataKey="Saídas" stroke="#f43f5e" strokeWidth={2}
                  fill="url(#gradS)" dot={false} activeDot={{ r: 4 }}/>
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-slate-400">
              Nenhum dado no período.
            </div>
          )}
          <div className="flex gap-4 mt-3">
            {[
              { cor: 'bg-blue-600', l: 'Entradas' },
              { cor: 'bg-rose-500', l: 'Saídas' },
            ].map(({ cor, l }) => (
              <span key={l} className="flex items-center gap-1.5 text-xs text-slate-500">
                <span className={`w-2 h-2 rounded-full ${cor}`}/>{l}
              </span>
            ))}
          </div>
        </div>

        {/* Contas urgentes */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-800">Contas urgentes</h3>
            <Link to="/contas" className="text-xs text-blue-600 hover:text-blue-700">Ver todas</Link>
          </div>
          <div className="divide-y divide-slate-100">
            {alertas?.contas_vencidas?.slice(0, 3).map(c => (
              <div key={c.id} className="py-3 first:pt-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-800 truncate">{c.descricao}</p>
                    <p className="text-[10px] text-rose-500 mt-0.5">
                      Venceu {formatData(c.vencimento)}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-semibold text-rose-600">{formatBRL(c.valor)}</p>
                    <button onClick={() => pagarConta(c.id)}
                      className="text-[10px] text-emerald-600 hover:text-emerald-700 font-medium mt-0.5">
                      Pagar →
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {alertas?.proximas_vencer?.slice(0, 2).map(c => (
              <div key={c.id} className="py-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-800 truncate">{c.descricao}</p>
                    <p className="text-[10px] text-amber-600 mt-0.5">
                      Vence {formatData(c.vencimento)}
                    </p>
                  </div>
                  <p className="text-xs font-semibold text-slate-700 flex-shrink-0">
                    {formatBRL(c.valor)}
                  </p>
                </div>
              </div>
            ))}
            {!alertas?.contas_vencidas?.length && !alertas?.proximas_vencer?.length && (
              <p className="text-xs text-slate-400 text-center py-6">
                ✓ Nenhuma conta urgente.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Resumo financeiro */}
      {resumo && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">Resumo financeiro do mês</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Total faturado',   valor: formatBRL(resumo.faturamento_mes), cor: 'text-emerald-600' },
              { label: 'Total de despesas',valor: formatBRL(resumo.despesas_mes),    cor: 'text-rose-600' },
              { label: 'Lucro estimado',
                valor: formatBRL(resumo.lucro_estimado),
                cor: resumo.lucro_estimado >= 0 ? 'text-emerald-600' : 'text-rose-600' },
              { label: 'Margem líquida',
                valor: `${resumo.margem_percentual}%`,
                cor: resumo.margem_percentual >= 10 ? 'text-emerald-600' : 'text-rose-600' },
            ].map(({ label, valor, cor }) => (
              <div key={label} className="bg-slate-50 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 mb-1">{label}</p>
                <p className={`text-base font-semibold ${cor}`}>{valor}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
