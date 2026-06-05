import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar.jsx'

/**
 * Layout principal do app autenticado.
 * [FIX INFO-003] Margem top no mobile usa CSS responsivo em vez de valor fixo.
 */
export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-4 pt-16 lg:pt-6 lg:p-6">
          <div className="page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
