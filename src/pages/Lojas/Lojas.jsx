import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import lojasService from '../../services/lojasService'
import { formatBRL } from '../../utils/formatters'
import { Modal } from '../../components/ui/Modal'
import { Confirm } from '../../components/ui/Confirm'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'

const FORM_VAZIO = { nome: '', codigo: '', endereco: '' }

function ModalLoja({ aberto, onFechar, onSalvo, loja }) {
  const [form, setForm]     = useState(FORM_VAZIO)
  const [salvando, setSalv] = useState(false)
  const editando = !!loja

  useEffect(() => {
    if (aberto) setForm(loja
      ? { nome: loja.nome || '', codigo: loja.codigo || '', endereco: loja.endereco || '' }
      : FORM_VAZIO
    )
  }, [aberto, loja])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.nome.trim()) return toast.error('Informe o nome da loja.')
    setSalv(true)
    try {
      const payload = {
        nome:     form.nome.trim(),
        codigo:   form.codigo.trim() || null,
        endereco: form.endereco.trim() || null,
      }
      if (editando) {
        await lojasService.atualizar(loja.id, payload)
        toast.success('Loja atualizada.')
      } else {
        await lojasService.criar(payload)
        toast.success('Loja cadastrada.')
      }
      onSalvo()
      onFechar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao salvar.')
    } finally { setSalv(false) }
  }

  return (
    <Modal aberto={aberto} onFechar={onFechar}
      titulo={editando ? 'Editar loja' : 'Nova unidade / loja'}
      largura="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label-base">Nome da loja *</label>
          <input className="input-base" placeholder="Ex: Loja 210, Valparaíso, Loja Centro..."
            value={form.nome} onChange={e => set('nome', e.target.value)} />
        </div>
        <div>
          <label className="label-base">Código (abreviação)</label>
          <input className="input-base" placeholder="Ex: 210, VAL, 209"
            value={form.codigo} onChange={e => set('codigo', e.target.value)} />
          <p className="text-xs text-slate-400 mt-1">Aparece no filtro e nos relatórios.</p>
        </div>
        <div>
          <label className="label-base">Endereço (opcional)</label>
          <input className="input-base" placeholder="Rua, número, bairro..."
            value={form.endereco} onChange={e => set('endereco', e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1"
            onClick={onFechar} disabled={salvando}>Cancelar</button>
          <button type="submit" className="btn-primary flex-1 justify-center"
            disabled={salvando}>
            {salvando
              ? <><Spinner size="sm" className="border-white/30 border-t-white"/>Salvando…</>
              : editando ? 'Salvar' : 'Cadastrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function Lojas() {
  const [lojas, setLojas]         = useState([])
  const [resumo, setResumo]       = useState([])
  const [carregando, setLoad]     = useState(true)
  const [modalAberto, setModal]   = useState(false)
  const [lojaEdit, setLojaEdit]   = useState(null)
  const [confirmDesativ, setConf] = useState(null)
  const [processando, setProc]    = useState(false)

  const carregar = useCallback(async () => {
    setLoad(true)
    try {
      const [rl, rr] = await Promise.all([
        lojasService.listar(),
        lojasService.resumoContas(),
      ])
      setLojas(rl.data.data || [])
      setResumo(rr.data.data || [])
    } catch { toast.error('Erro ao carregar lojas.') }
    finally { setLoad(false) }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  const desativar = async () => {
    setProc(true)
    try {
      await lojasService.desativar(confirmDesativ.id)
      toast.success('Loja desativada.')
      setConf(null)
      carregar()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erro ao desativar.')
    } finally { setProc(false) }
  }

  const totalPendente = resumo.reduce((a, l) => a + (l.total_pendente || 0), 0)
  const totalPago     = resumo.reduce((a, l) => a + (l.total_pago || 0), 0)
  const totalVencidas = resumo.reduce((a, l) => a + (l.contas_vencidas || 0), 0)

  return (
    <div className="max-w-7xl mx-auto space-y-5 page-enter">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Lojas / Unidades</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Gerencie as unidades e filtre contas por loja
          </p>
        </div>
        <button className="btn-primary" onClick={() => { setLojaEdit(null); setModal(true) }}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth={2.5}>
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Nova loja
        </button>
      </div>

      {/* KPIs globais */}
      <div className="grid grid-cols-3 gap-4">
        <div className="kpi-card">
          <p className="kpi-label">Total de lojas</p>
          <p className="kpi-value">{lojas.length}</p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Contas pendentes (todas)</p>
          <p className={`kpi-value ${totalVencidas > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
            {formatBRL(totalPendente)}
          </p>
        </div>
        <div className="kpi-card">
          <p className="kpi-label">Pagas no período</p>
          <p className="kpi-value text-emerald-600">{formatBRL(totalPago)}</p>
        </div>
      </div>

      {/* Cards por loja */}
      {carregando ? <PageLoader /> : lojas.length === 0 ? (
        <div className="card">
          <EmptyState
            icone={
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth={1.5}>
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
            }
            titulo="Nenhuma loja cadastrada"
            descricao="Cadastre as unidades para filtrar contas a pagar por loja."
            acao={
              <button className="btn-primary" onClick={() => setModal(true)}>
                Cadastrar loja
              </button>
            }
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {lojas.map(loja => {
            const res = resumo.find(r => r.loja_id === loja.id) || {}
            const temAlerta = (res.contas_vencidas || 0) > 0

            return (
              <div key={loja.id}
                className={`card p-5 border-l-4 ${temAlerta ? 'border-l-rose-500' : 'border-l-blue-500'}`}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      {loja.codigo && (
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                          {loja.codigo}
                        </span>
                      )}
                      {temAlerta && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-rose-100 text-rose-700">
                          ⚠ {res.contas_vencidas} vencida(s)
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-semibold text-slate-800 mt-1.5">{loja.nome}</h3>
                    {loja.endereco && (
                      <p className="text-xs text-slate-400 mt-0.5">{loja.endereco}</p>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => { setLojaEdit(loja); setModal(true) }}
                      className="btn-ghost text-xs py-1 px-2">
                      Editar
                    </button>
                    <button
                      onClick={() => setConf(loja)}
                      className="btn-ghost text-xs py-1 px-2 text-rose-400 hover:text-rose-600">
                      ✕
                    </button>
                  </div>
                </div>

                {/* Métricas da loja */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                  <div>
                    <p className="text-[10px] text-slate-400 mb-0.5">Pendente</p>
                    <p className={`text-sm font-semibold ${
                      (res.total_pendente || 0) > 0 ? 'text-rose-600' : 'text-slate-400'
                    }`}>
                      {formatBRL(res.total_pendente || 0)}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-400 mb-0.5">Pago</p>
                    <p className="text-sm font-semibold text-emerald-600">
                      {formatBRL(res.total_pago || 0)}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Tabela resumo */}
      {resumo.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-800">Resumo financeiro por unidade</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 text-slate-300">
                  {['Cód.','Loja','Pendente / Vencido','Pago','Vencidas'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {resumo.map((r, i) => (
                  <tr key={r.loja_id || 'sem'} className={`hover:bg-slate-50/60 ${i%2===0?'':'bg-slate-50/30'}`}>
                    <td className="px-4 py-3">
                      {r.loja_codigo
                        ? <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">{r.loja_codigo}</span>
                        : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">{r.loja_nome}</td>
                    <td className="px-4 py-3 font-semibold text-rose-600">{formatBRL(r.total_pendente)}</td>
                    <td className="px-4 py-3 font-semibold text-emerald-600">{formatBRL(r.total_pago)}</td>
                    <td className="px-4 py-3">
                      {r.contas_vencidas > 0
                        ? <span className="text-xs font-medium px-2 py-0.5 rounded bg-rose-100 text-rose-700">{r.contas_vencidas}</span>
                        : <span className="text-xs text-slate-400">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ModalLoja aberto={modalAberto} onFechar={() => setModal(false)}
        onSalvo={carregar} loja={lojaEdit} />

      <Confirm aberto={!!confirmDesativ} onFechar={() => setConf(null)}
        onConfirmar={desativar} titulo="Desativar loja"
        mensagem={`Desativar "${confirmDesativ?.nome}"? As contas vinculadas continuam existindo.`}
        carregando={processando} />
    </div>
  )
}
