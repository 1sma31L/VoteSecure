import { useState } from 'react'
import { useServices, useInitKeys, useResetAll } from '../api'
import Alert from '../components/Alert'

const SVC_COLORS = {
  commissioner: 'neon-blue',
  administrator: 'neon-cyan',
  anonymiser: 'neon-orange',
  counter: 'neon-green',
}

const colorMap = {
  'neon-blue': { bg: 'bg-neon-blue/10', border: 'border-neon-blue/20', text: 'text-neon-blue', dot: 'bg-neon-blue' },
  'neon-cyan': { bg: 'bg-neon-cyan/10', border: 'border-neon-cyan/20', text: 'text-neon-cyan', dot: 'bg-neon-cyan' },
  'neon-green': { bg: 'bg-neon-green/10', border: 'border-neon-green/20', text: 'text-neon-green', dot: 'bg-neon-green' },
  'neon-orange': { bg: 'bg-neon-orange/10', border: 'border-neon-orange/20', text: 'text-neon-orange', dot: 'bg-neon-orange' },
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
    <div className="max-w-3xl mx-auto px-6 py-12">
      <div className="mb-8">
        <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-[0.2em] mb-2 font-mono">Configuration</p>
        <h2 className="font-display text-2xl font-black text-white tracking-tight">Services</h2>
        <p className="text-slate-400 mt-2">Initialisez les clés RSA avant d'ouvrir un scrutin.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        {isLoading ? (
          <div className="col-span-2 text-center py-8 text-slate-500">Chargement…</div>
        ) : (
          svcEntries.map(([key, svc]) => {
            const online = svc.status === 'ok'
            const c = colorMap[SVC_COLORS[key]] || colorMap['neon-blue']
            return (
              <div key={key} className={`bg-surface-2 border ${c.border} rounded-2xl p-5`}>
                <div className="flex items-center gap-3 mb-3">
                  <span className={`w-3 h-3 rounded-full ${online ? `${c.dot} animate-pulse` : 'bg-slate-600'}`} />
                  <span className={`font-bold ${online ? c.text : 'text-slate-500'} capitalize`}>{key}</span>
                </div>
                <div className="text-xs text-slate-500 font-mono">{svc.url}</div>
                <div className={`text-xs font-semibold mt-1 ${online ? c.text : 'text-slate-600'}`}>
                  {online ? 'En ligne' : 'Hors ligne'}
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6">
        <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-2 font-mono">Initialisation rapide</p>
        <p className="text-sm text-slate-400 mb-5">
          Lance la génération des clés RSA sur l'administrateur et le décompteur. À faire avant d'ouvrir un scrutin.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleInit}
            disabled={initKeys.isPending}
            className="inline-flex items-center gap-2 bg-brand-600 text-white font-bold px-5 py-2.5 rounded-xl hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-lg shadow-brand-600/20"
          >
            {initKeys.isPending && <Spinner />}
            ⚙ Initialiser les clés RSA
          </button>
          <button
            onClick={handleReset}
            disabled={resetAll.isPending}
            className="inline-flex items-center gap-2 bg-neon-pink/20 border border-neon-pink/30 text-neon-pink font-bold px-5 py-2.5 rounded-xl hover:bg-neon-pink/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            ↺ Réinitialiser tout
          </button>
        </div>
        {msg && (
          <div className="mt-4">
            <Alert type={msg.type}>{msg.text}</Alert>
          </div>
        )}
      </div>
    </div>
  )
}

function Spinner() {
  return <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
}
