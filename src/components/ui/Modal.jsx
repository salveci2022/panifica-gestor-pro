import { useEffect } from 'react'

export function Modal({ aberto, onFechar, titulo, children, largura = 'max-w-lg' }) {
  useEffect(() => {
    if (aberto) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [aberto])

  if (!aberto) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/60" onClick={onFechar} />
      <div className={`relative w-full ${largura} bg-white rounded-xl shadow-2xl animate-[slideUp_0.2s_ease-out]`}>
        {titulo && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h2 className="text-base font-semibold text-slate-900">{titulo}</h2>
            <button onClick={onFechar} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}
