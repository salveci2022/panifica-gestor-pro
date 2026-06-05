export function EmptyState({ icone, titulo, descricao, acao }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-slate-400">
        {icone}
      </div>
      <p className="text-sm font-medium text-slate-700 mb-1">{titulo}</p>
      {descricao && <p className="text-xs text-slate-400 mb-4 max-w-xs">{descricao}</p>}
      {acao}
    </div>
  )
}
