const styles = {
  success: 'bg-neon-green/10 border-neon-green/20 text-neon-green',
  error: 'bg-neon-pink/10 border-neon-pink/20 text-neon-pink',
  info: 'bg-neon-blue/10 border-neon-blue/20 text-neon-blue',
  warning: 'bg-neon-orange/10 border-neon-orange/20 text-neon-orange',
}

const icons = { success: '✓', error: '✗', info: 'i', warning: '!' }

const iconBg = {
  success: 'bg-neon-green/20 text-neon-green',
  error: 'bg-neon-pink/20 text-neon-pink',
  info: 'bg-neon-blue/20 text-neon-blue',
  warning: 'bg-neon-orange/20 text-neon-orange',
}

export default function Alert({ type = 'info', children, className = '' }) {
  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-xl border text-sm leading-relaxed ${styles[type]} ${className}`}>
      <span className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[0.65rem] font-extrabold mt-0.5 ${iconBg[type]}`}>
        {icons[type]}
      </span>
      <span>{children}</span>
    </div>
  )
}
