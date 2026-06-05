export const validarEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
export const validarSenha = (senha) => senha.length >= 8
export const campoObrigatorio = (valor) => valor !== null && valor !== undefined && String(valor).trim() !== ''
export const validarValor = (v) => parseFloat(v) > 0
