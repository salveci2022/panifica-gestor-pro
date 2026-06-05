export function Badge({ status }) {
  const map = {
    pendente:  { label: 'Pendente',  cls: 'bg-amber-50 text-amber-700 border border-amber-200' },
    paga:      { label: 'Paga',      cls: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
    vencida:   { label: 'Vencida',   cls: 'bg-rose-50 text-rose-700 border border-rose-200' },
    cancelada: { label: 'Cancelada', cls: 'bg-slate-100 text-slate-500 border border-slate-200' },
    ativo:     { label: 'Ativo',     cls: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
    inativo:   { label: 'Inativo',   cls: 'bg-slate-100 text-slate-500 border border-slate-200' },
  }
  const item = map[status] || { label: status, cls: 'bg-slate-100 text-slate-600' }
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${item.cls}`}>{item.label}</span>
}
