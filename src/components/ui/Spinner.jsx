export function Spinner({ size = 'md', className = '' }) {
  const s = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }[size]
  return (
    <div className={`${s} ${className} animate-spin rounded-full border-2 border-slate-200 border-t-blue-600`} />
  )
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center h-48">
      <Spinner size="lg" />
    </div>
  )
}
