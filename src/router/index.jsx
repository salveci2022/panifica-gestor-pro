import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { AppLayout } from '../components/layout/AppLayout.jsx'
import Login        from '../pages/Login/Login.jsx'
import Dashboard    from '../pages/Dashboard/Dashboard.jsx'
import ContasPagar  from '../pages/ContasPagar/ContasPagar.jsx'
import Fornecedores from '../pages/Fornecedores/Fornecedores.jsx'
import FluxoCaixa   from '../pages/FluxoCaixa/FluxoCaixa.jsx'
import Estoque      from '../pages/Estoque/Estoque.jsx'
import Compras      from '../pages/Compras/Compras.jsx'
import Producao     from '../pages/Producao/Producao.jsx'
import Lojas        from '../pages/Lojas/Lojas.jsx'

function RotaProtegida({ children }) {
  const auth = useAuthStore(s => s.estaAutenticado())
  return auth ? children : <Navigate to="/login" replace />
}

function RotaPublica({ children }) {
  const auth = useAuthStore(s => s.estaAutenticado())
  return auth ? <Navigate to="/dashboard" replace /> : children
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<RotaPublica><Login /></RotaPublica>} />
      <Route element={<RotaProtegida><AppLayout /></RotaProtegida>}>
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/contas"       element={<ContasPagar />} />
        <Route path="/fornecedores" element={<Fornecedores />} />
        <Route path="/fluxo-caixa"  element={<FluxoCaixa />} />
        <Route path="/estoque"      element={<Estoque />} />
        <Route path="/compras"      element={<Compras />} />
        <Route path="/producao"     element={<Producao />} />
        <Route path="/lojas"        element={<Lojas />} />
      </Route>
      <Route path="/"  element={<Navigate to="/dashboard" replace />} />
      <Route path="*"  element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
