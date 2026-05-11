import { useState } from 'react'
import { useServices, useInitKeys, useResetAll } from '../api'
import Alert from '../components/Alert'

function Btn({ slug, alt, onClick, disabled, className = '' }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled}
      className={`clay-img-btn ${className}`}>
      <img src={`/assets/buttons/btn-${slug}.png`} alt={alt}
        className="block h-auto pointer-events-none select-none" draggable={false} />
    </button>
  )
}

const SVC_META = {
  commissioner: { colorKey: 'blue',  icon: '👤' },
  administrator: { colorKey: 'green', icon: '🔐' },
  anonymiser:    { colorKey: 'amber', icon: '🎭' },
  counter:       { colorKey: 'green', icon: '📊' },
}

const dotColors = {
  blue:  'bg-[#1E3A6E]',
  green: 'bg-[#3D7A4E]',
  amber: 'bg-[#B8860B]',
}

export default function Services() {
  const { data: services, isLoading } = useServices()
  const initKeys = useInitKeys()
  const resetAll = useResetAll()
  const [msg, setMsg] = useState(null)

  const handleInit = async () => {
    setMsg(null)
    try {
      const res = await initKeys.mutateAsync()
      if (res.admin?.ok && res.counter?.ok) {
        setMsg({ type: 'success', text: 'Clés RSA générées avec succès sur l\'administrateur et le décompteur.' })
      } else {
        setMsg({ type: 'error', text: 'La génération des clés a échoué.' })
      }
    } catch (e) {
      setMsg({ type: 'error', text: `Erreur réseau : ${e.message}` })
    }
  }

  const handleReset = async () => {
    if (!confirm('Réinitialiser tous les services ? Cette action efface toutes les données.')) return
    setMsg(null)
    try {
      await resetAll.mutateAsync()
      setMsg({ type: 'info', text: 'Tous les services ont été réinitialisés.' })
    } catch (e) {
      setMsg({ type: 'error', text: `Erreur : ${e.message}` })
    }
  }

  const svcEntries = services ? Object.entries(services) : []

  return (
    <div className="clay-page-inner">
      <div className="clay-page-header">
        <p className="clay-label">Configuration</p>
        <h2 className="clay-page-title">Services</h2>
        <p className="clay-page-sub">Initialisez les clés RSA avant d'ouvrir un scrutin.</p>
      </div>

      {/* Service status grid */}
      <div className="clay-services-status-grid mb-8">
        {isLoading ? (
          <div className="col-span-2 text-center py-8 clay-muted">Chargement…</div>
        ) : (
          svcEntries.map(([key, svc]) => {
            const meta = SVC_META[key] || { colorKey: 'blue', icon: '⚙' }
            const online = svc.status === 'ok'
            return (
              <div key={key} className="clay-svc-status-card">
                <div className="clay-svc-icon">{meta.icon}</div>
                <div className="clay-svc-info">
                  <span className="clay-svc-name capitalize">{key}</span>
                  <span className="clay-svc-url">{svc.url}</span>
                </div>
                <div className="clay-svc-status-row">
                  <span className={`clay-dot ${online ? `${dotColors[meta.colorKey]} animate-pulse` : 'bg-[#BFB9AF]'}`} />
                  <span className={`clay-svc-status-label ${online ? 'clay-svc-online' : 'clay-svc-offline'}`}>
                    {online ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Init panel */}
      <div className="clay-card">
        <p className="clay-label mb-2">Initialisation rapide</p>
        <p className="clay-page-sub mb-5">
          Lance la génération des clés RSA sur l'administrateur et le décompteur. À faire avant d'ouvrir un scrutin.
        </p>
        <div className="clay-btn-row">
          <Btn slug="init-keys" alt="Initialiser les clés RSA" onClick={handleInit} disabled={initKeys.isPending} />
          <Btn slug="reset"     alt="Réinitialiser tout"       onClick={handleReset} disabled={resetAll.isPending} />
        </div>
        {msg && <Alert type={msg.type} className="mt-4">{msg.text}</Alert>}
      </div>
    </div>
  )
}
