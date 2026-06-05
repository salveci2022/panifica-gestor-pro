import { Modal } from './Modal'

export function Confirm({ aberto, onFechar, onConfirmar, titulo, mensagem, carregando }) {
  return (
    <Modal aberto={aberto} onFechar={onFechar} titulo={titulo} largura="max-w-sm">
      <p className="text-sm text-slate-600 mb-6">{mensagem}</p>
      <div className="flex gap-3 justify-end">
        <button className="btn-secondary" onClick={onFechar} disabled={carregando}>Cancelar</button>
        <button className="btn-danger" onClick={onConfirmar} disabled={carregando}>
          {carregando ? 'Processando…' : 'Confirmar'}
        </button>
      </div>
    </Modal>
  )
}
