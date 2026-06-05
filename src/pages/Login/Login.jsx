import { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../../hooks/useAuth'
import { validarEmail } from '../../utils/validators'

export default function Login() {
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', senha: '' })
  const [carregando, setCarregando] = useState(false)
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [erros, setErros] = useState({})

  const validar = () => {
    const e = {}
    if (!form.email) e.email = 'E-mail obrigatório'
    else if (!validarEmail(form.email)) e.email = 'E-mail inválido'
    if (!form.senha) e.senha = 'Senha obrigatória'
    setErros(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validar()) return
    setCarregando(true)
    try {
      await login(form.email.trim().toLowerCase(), form.senha)
    } catch (err) {
      const msg = err.response?.data?.error || 'E-mail ou senha inválidos.'
      toast.error(msg)
      setErros({ geral: msg })
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Painel esquerdo — identidade */}
      <div className="hidden lg:flex lg:w-[420px] bg-slate-900 flex-col justify-between p-10 flex-shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400 tracking-wide leading-tight">PANIFICA GESTOR PRO</p>
              <p className="text-xs text-white/40">por SPYNET Tecnologia</p>
            </div>
          </div>

          <h1 className="text-3xl font-semibold text-white leading-snug mb-4">
            Gestão financeira<br />
            <span className="text-blue-400">para padarias</span>
          </h1>
          <p className="text-sm text-white/40 leading-relaxed">
            Controle contas a pagar, fornecedores, fluxo de caixa e muito mais — em um único sistema.
          </p>
        </div>

        <div className="space-y-3">
          {[
            'Dashboard com KPIs em tempo real',
            'Alertas automáticos de vencimento',
            'Relatórios PDF com 1 clique',
            'Multi-usuário com controle de acesso',
          ].map((item) => (
            <div key={item} className="flex items-center gap-2.5 text-sm text-white/40">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />
              {item}
            </div>
          ))}
          <p className="text-xs text-white/25 pt-4">CNPJ 64.000.808/0001-51</p>
        </div>
      </div>

      {/* Painel direito — formulário */}
      <div className="flex-1 flex items-center justify-center p-6 bg-slate-50">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-slate-900 mb-1">Acesse sua conta</h2>
            <p className="text-base text-slate-500">Digite seu e-mail e senha para continuar.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* E-mail */}
            <div>
              <label className="label-base">E-mail</label>
              <input
                type="email"
                className={`input-base ${erros.email ? 'border-rose-400 focus:ring-rose-500/20 focus:border-rose-500' : ''}`}
                placeholder="joao@padaria.com.br"
                value={form.email}
                onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))}
                disabled={carregando}
                autoComplete="email"
                autoFocus
              />
              {erros.email && <p className="text-xs text-rose-500 mt-1">{erros.email}</p>}
            </div>

            {/* Senha */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="label-base mb-0">Senha</label>
                <Link to="/recuperar-senha" className="text-xs text-blue-600 hover:text-blue-700 transition-colors">
                  Esqueci minha senha
                </Link>
              </div>
              <div className="relative">
                <input
                  type={mostrarSenha ? 'text' : 'password'}
                  className={`input-base pr-10 ${erros.senha ? 'border-rose-400 focus:ring-rose-500/20 focus:border-rose-500' : ''}`}
                  placeholder="••••••••"
                  value={form.senha}
                  onChange={(e) => setForm(f => ({ ...f, senha: e.target.value }))}
                  disabled={carregando}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setMostrarSenha(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  tabIndex={-1}
                >
                  {mostrarSenha ? (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
              {erros.senha && <p className="text-xs text-rose-500 mt-1">{erros.senha}</p>}
            </div>

            {erros.geral && (
              <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                <svg className="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {erros.geral}
              </div>
            )}

            <button
              type="submit"
              className="w-full btn-primary justify-center py-2.5 text-sm font-medium mt-2"
              disabled={carregando}
            >
              {carregando ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Entrando…
                </>
              ) : 'Entrar no sistema'}
            </button>
          </form>

          <p className="text-center text-xs text-slate-400 mt-6">
            Conexão segura · Seus dados são protegidos pela LGPD
          </p>
        </div>
      </div>
    </div>
  )
}
