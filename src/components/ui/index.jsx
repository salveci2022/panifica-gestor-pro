import { clsx } from 'clsx'

// ─── Badge / Pill ─────────────────────────────────────────────────────────────
export function Pill({ status, children, className }) {
  const map = {
    pendente:  'pill-pendente',
    paga:      'pill-paga',
    vencida:   'pill-vencida',
    cancelada: 'pill-cancelada',
    info:      'pill-info',
  }
  return (
    <span className={clsx('pill', map[status] || 'pill-info', className)}>
      {children}
    </span>
  )
}

// ─── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ size = 'md', className }) {
  const s = { sm: 'w-3.5 h-3.5', md: 'w-5 h-5', lg: 'w-7 h-7' }[size]
  return (
    <svg
      className={clsx('animate-spin text-brand', s, className)}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
export function Skeleton({ className }) {
  return <div className={clsx('animate-pulse-slow bg-gray-100 rounded', className)} />
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
export function KpiCard({ label, valor, delta, deltaUp, icon, cor, carregando }) {
  const corMap = {
    verde:  { bg: 'bg-fin-green-bg', text: 'text-fin-green', icon: 'text-fin-green' },
    vermelho: { bg: 'bg-fin-red-bg', text: 'text-fin-red', icon: 'text-fin-red' },
    azul:   { bg: 'bg-brand-pale', text: 'text-brand', icon: 'text-brand' },
    amber:  { bg: 'bg-fin-amber-bg', text: 'text-fin-amber', icon: 'text-fin-amber' },
    neutro: { bg: 'bg-gray-100', text: 'text-gray-600', icon: 'text-gray-400' },
  }
  const c = corMap[cor] || corMap.neutro

  return (
    <div className="kpi-card animate-fade-up">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        {icon && (
          <span className={clsx('w-7 h-7 rounded-lg flex items-center justify-center text-sm', c.bg, c.icon)}>
            <i className={`ti ${icon}`} />
          </span>
        )}
      </div>
      {carregando ? (
        <Skeleton className="h-7 w-28 mb-1" />
      ) : (
        <div className={clsx('text-2xl font-semibold tracking-tight', c.text)}>{valor}</div>
      )}
      {delta && (
        <div className={clsx('text-xs mt-1', deltaUp ? 'text-fin-green' : 'text-fin-red')}>
          {deltaUp ? '↑' : '↓'} {delta}
        </div>
      )}
    </div>
  )
}

// ─── Modal ────────────────────────────────────────────────────────────────────
export function Modal({ aberto, fechar, titulo, children, largura = 'max-w-lg' }) {
  if (!aberto) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => e.target === e.currentTarget && fechar()}
    >
      <div className={clsx('card w-full animate-fade-up', largura)}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-black/[0.06]">
          <h3 className="text-md font-semibold text-gray-800">{titulo}</h3>
          <button onClick={fechar} className="btn-ghost w-7 h-7 p-0 flex items-center justify-center">
            <i className="ti ti-x text-base" />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </div>
    </div>
  )
}

// ─── Empty State ──────────────────────────────────────────────────────────────
export function EmptyState({ icon = 'ti-inbox', titulo, descricao, acao }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
        <i className={clsx('ti', icon, 'text-2xl text-gray-300')} />
      </div>
      <p className="text-sm font-medium text-gray-500 mb-1">{titulo}</p>
      {descricao && <p className="text-xs text-gray-400 mb-4 max-w-xs">{descricao}</p>}
      {acao}
    </div>
  )
}

// ─── Confirm Dialog ───────────────────────────────────────────────────────────
export function ConfirmDialog({ aberto, fechar, titulo, mensagem, onConfirmar, carregando }) {
  return (
    <Modal aberto={aberto} fechar={fechar} titulo={titulo} largura="max-w-sm">
      <p className="text-sm text-gray-500 mb-5">{mensagem}</p>
      <div className="flex gap-2 justify-end">
        <button onClick={fechar} className="btn-secondary">Cancelar</button>
        <button onClick={onConfirmar} disabled={carregando} className="btn-danger">
          {carregando ? <Spinner size="sm" /> : 'Confirmar'}
        </button>
      </div>
    </Modal>
  )
}

// ─── Form Field ───────────────────────────────────────────────────────────────
export function FormField({ label, erro, children, obrigatorio }) {
  return (
    <div>
      <label className="label">
        {label}
        {obrigatorio && <span className="text-fin-red ml-0.5">*</span>}
      </label>
      {children}
      {erro && <p className="text-xs text-fin-red mt-1">{erro}</p>}
    </div>
  )
}

// ─── Select ───────────────────────────────────────────────────────────────────
export function Select({ value, onChange, options, placeholder, className, disabled }) {
  return (
    <select
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={clsx('input-field', className)}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

// ─── Paginação ────────────────────────────────────────────────────────────────
export function Paginacao({ meta, onChange }) {
  if (!meta || meta.total_paginas <= 1) return null
  return (
    <div className="flex items-center justify-between pt-3 border-t border-black/[0.05] mt-2">
      <span className="text-xs text-gray-400">
        {meta.total} registro{meta.total !== 1 ? 's' : ''}
      </span>
      <div className="flex gap-1">
        <button
          onClick={() => onChange(meta.pagina - 1)}
          disabled={!meta.tem_anterior}
          className="btn-ghost px-2 py-1 text-xs disabled:opacity-30"
        >
          <i className="ti ti-chevron-left" />
        </button>
        <span className="text-xs text-gray-500 flex items-center px-2">
          {meta.pagina} / {meta.total_paginas}
        </span>
        <button
          onClick={() => onChange(meta.pagina + 1)}
          disabled={!meta.tem_proxima}
          className="btn-ghost px-2 py-1 text-xs disabled:opacity-30"
        >
          <i className="ti ti-chevron-right" />
        </button>
      </div>
    </div>
  )
}
