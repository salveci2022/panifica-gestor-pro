import { clsx } from 'clsx'

export default function PageHeader({ titulo, subtitulo, acoes, className }) {
  return (
    <div className={clsx('flex items-center justify-between mb-5', className)}>
      <div>
        <h1 className="text-lg font-semibold text-gray-800 leading-tight">{titulo}</h1>
        {subtitulo && <p className="text-xs text-gray-400 mt-0.5">{subtitulo}</p>}
      </div>
      {acoes && <div className="flex items-center gap-2">{acoes}</div>}
    </div>
  )
}
