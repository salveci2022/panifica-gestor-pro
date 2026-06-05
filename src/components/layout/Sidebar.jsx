import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth.js'

const MENU = [
  { secao: 'PRINCIPAL', itens: [
    { to: '/dashboard',    label: 'Dashboard' },
  ]},
  { secao: 'FINANCEIRO', itens: [
    { to: '/contas',       label: 'Contas a Pagar' },
    { to: '/fluxo-caixa',  label: 'Fluxo de Caixa' },
  ]},
  { secao: 'OPERAÇÃO', itens: [
    { to: '/fornecedores', label: 'Fornecedores' },
    { to: '/lojas',        label: 'Lojas / Unidades' },
    { to: '/compras',      label: 'Compras' },
    { to: '/estoque',      label: 'Estoque' },
    { to: '/producao',     label: 'Produção Diária' },
  ]},
]

export function Sidebar() {
  const { usuario, tenant, logout } = useAuth()
  const [aberta, setAberta] = useState(false)

  return (
    <>
      <button
        className="lg:hidden fixed top-3 left-3 z-50 p-2 bg-slate-900 rounded-lg text-white shadow-lg"
        onClick={() => setAberta(v => !v)} aria-label="Menu">
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          {aberta ? <path d="M18 6L6 18M6 6l12 12"/> : <path d="M3 12h18M3 6h18M3 18h18"/>}
        </svg>
      </button>

      {aberta && (
        <div className="lg:hidden fixed inset-0 bg-slate-900/60 z-40" onClick={() => setAberta(false)}/>
      )}

      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-[218px] min-h-screen bg-slate-900 flex flex-col flex-shrink-0
        transform transition-transform duration-200
        ${aberta ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="px-5 py-5 border-b border-white/[0.07]">
          <div className="text-sm font-bold text-blue-400 tracking-wide mb-0.5">PANIFICA GESTOR PRO</div>
          <div className="text-xs text-white/40 truncate">{tenant?.nome || 'Sistema'}</div>
        </div>

        <nav className="flex-1 py-4 px-3 overflow-y-auto">
          {MENU.map(({ secao, itens }) => (
            <div key={secao} className="mb-3">
              <p className="text-[11px] font-semibold text-white/25 tracking-[1px] px-2 mb-1.5 uppercase">{secao}</p>
              {itens.map(({ to, label }) => (
                <NavLink key={to} to={to} onClick={() => setAberta(false)}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 rounded-lg text-sm mb-0.5 transition-all duration-150 border-l-2 ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-300 border-l-blue-500 font-medium'
                        : 'text-white/40 border-l-transparent hover:bg-white/5 hover:text-white/70'
                    }`
                  }>
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/[0.07]">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-full bg-blue-800 flex items-center justify-center text-[10px] font-bold text-blue-300 flex-shrink-0">
              {usuario?.nome?.charAt(0).toUpperCase() || '?'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-white/60 truncate">{usuario?.nome}</p>
              <p className="text-[11px] text-white/30 capitalize">{usuario?.perfil}</p>
            </div>
          </div>
          <button onClick={logout} className="w-full text-left text-xs text-white/25 hover:text-rose-400 transition-colors py-1">
            Sair do sistema
          </button>
        </div>
      </aside>
    </>
  )
}
