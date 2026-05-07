import { useCounterState } from '../api'
import { useNavigate } from 'react-router-dom'

export default function Results() {
  const { data: counterState, isLoading } = useCounterState()
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="max-w-xl mx-auto px-6 py-16 text-center text-slate-500">
        Chargement…
      </div>
    )
  }

  const results = counterState?.results || {}
  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const isDone = counterState?.phase === 'done'

  if (!isDone) {
    return (
      <div className="max-w-xl mx-auto px-6 py-16 text-center">
        <h2 className="font-display text-2xl font-black text-white mb-3">Pas encore de résultats</h2>
        <p className="text-slate-400 mb-6">Le scrutin n'a pas encore été clôturé ou dépouillé.</p>
        <button
          onClick={() => navigate('/')}
          className="bg-brand-600 text-white font-bold px-5 py-2.5 rounded-xl hover:bg-brand-500 transition-colors shadow-lg shadow-brand-600/20"
        >
          ← Retour à l'accueil
        </button>
      </div>
    )
  }

  const winner = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  return (
    <div className="max-w-xl mx-auto px-6 py-12">
      <p className="text-[0.7rem] font-bold text-neon-green uppercase tracking-[0.2em] mb-2 font-mono">Dépouillement terminé</p>
      <h2 className="font-display text-2xl font-black text-white tracking-tight mb-8">Résultats du scrutin</h2>

      {winner && (
        <div className="bg-gradient-to-br from-brand-900 to-brand-700 rounded-2xl p-8 text-center mb-8 shadow-xl shadow-brand-900/50">
          <div className="text-[0.6rem] font-bold tracking-[0.15em] uppercase text-white/40 mb-2 font-mono">◈ Vainqueur du scrutin</div>
          <div className="font-display text-3xl font-black text-white">{winner[0]}</div>
          <div className="text-white/50 text-sm font-mono mt-2">{winner[1]} vote{winner[1] > 1 ? 's' : ''} · {totalValid} total</div>
        </div>
      )}

      <div className="space-y-4">
        {Object.entries(results)
          .sort((a, b) => b[1] - a[1])
          .map(([opt, v]) => {
            const pct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
            return (
              <div key={opt}>
                <div className="flex justify-between mb-1.5">
                  <span className="font-bold text-white">{opt}</span>
                  <span className="text-slate-500 font-mono text-sm">{v} vote{v > 1 ? 's' : ''} — {pct}%</span>
                </div>
                <div className="h-3 bg-surface-4 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${
                      opt === winner?.[0]
                        ? 'bg-gradient-to-r from-neon-blue to-neon-cyan'
                        : 'bg-surface-5'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}
