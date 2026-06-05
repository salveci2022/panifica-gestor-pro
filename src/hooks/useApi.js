import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'

export function useApi() {
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

  const chamar = useCallback(async (fn, opcoes = {}) => {
    const {
      onSucesso,
      mensagemSucesso,
      mensagemErro,
      silencioso = false,
    } = opcoes

    setCarregando(true)
    setErro(null)

    try {
      const resultado = await fn()
      if (mensagemSucesso && !silencioso) {
        toast.success(mensagemSucesso)
      }
      if (onSucesso) onSucesso(resultado)
      return resultado
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        mensagemErro ||
        'Ocorreu um erro. Tente novamente.'
      setErro(msg)
      if (!silencioso) toast.error(msg)
      return null
    } finally {
      setCarregando(false)
    }
  }, [])

  return { carregando, erro, chamar }
}
