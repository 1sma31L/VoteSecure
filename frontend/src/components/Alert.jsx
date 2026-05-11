const styles = {
  success: 'clay-alert--success',
  error:   'clay-alert--error',
  info:    'clay-alert--info',
  warning: 'clay-alert--warning',
}

const icons = { success: '✓', error: '✗', info: 'i', warning: '!' }

export default function Alert({ type = 'info', children, className = '' }) {
  return (
    <div className={`clay-alert ${styles[type]} ${className}`}>
      <span className={`clay-alert-icon clay-alert-icon--${type}`}>{icons[type]}</span>
      <span className="clay-alert-text">{children}</span>
    </div>
  )
}
