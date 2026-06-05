import { useState, useEffect, useCallback } from 'react'

export function useFetch(fn, deps = [], opcoes = {}) {
  const { imediato = true } = opcoes
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(imediato)
  const [erro, setErro] = useState(null)

  const executar = useCallback(async (...args) => {
    setCarregando(true)
    setErro(null)
    try {
      const resp = await fn(...args)
      setDados(resp.data?.data ?? resp.data)
      return resp.data?.data
    } catch (e) {
      const msg = e.response?.data?.error || 'Erro ao carregar dados.'
      setErro(msg)
      throw e
    } finally {
      setCarregando(false)
    }
  }, deps)

  useEffect(() => {
    if (imediato) executar()
  }, [executar])

  return { dados, carregando, erro, recarregar: executar }
}
