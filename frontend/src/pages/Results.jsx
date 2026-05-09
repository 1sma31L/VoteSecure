import { useCounterState } from '../api'
import { useNavigate } from 'react-router-dom'

function Btn({ slug, alt, onClick, className = '' }) {
  return (
    <button type="button" onClick={onClick} className={`clay-img-btn ${className}`}>
      <img src={`/assets/buttons/btn-${slug}.png`} alt={alt}
        className="block h-auto pointer-events-none select-none" draggable={false} />
    </button>
  )
}

export default function Results() {
  const { data: counterState, isLoading } = useCounterState()
  const navigate = useNavigate()

  if (isLoading) {
    return <div className="clay-page-inner clay-center clay-muted py-16">Chargement…</div>
  }

  const results   = counterState?.results || {}
  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const isDone    = counterState?.phase === 'done'

  if (!isDone) {
    return (
      <div className="clay-page-inner clay-center">
        <h2 className="clay-page-title mb-3">Pas encore de résultats</h2>
        <p className="clay-page-sub mb-6">Le scrutin n'a pas encore été clôturé ou dépouillé.</p>
        <Btn slug="retour" alt="Retour à l'accueil" onClick={() => navigate('/')} />
      </div>
    )
  }

  const winner = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  return (
    <div className="clay-page-inner">
      <p className="clay-label clay-label--green">Dépouillement terminé</p>
      <h2 className="clay-page-title mb-8">Résultats du scrutin</h2>

      {winner && (
        <div className="clay-winner-box clay-winner-box--lg mb-8">
          <div className="clay-winner-eyebrow">◈ Vainqueur du scrutin</div>
          <div className="clay-winner-name clay-winner-name--lg">{winner[0]}</div>
          <div className="clay-winner-sub">{winner[1]} vote{winner[1] > 1 ? 's' : ''} · {totalValid} total</div>
        </div>
      )}

      <div className="clay-results-list">
        {Object.entries(results).sort((a, b) => b[1] - a[1]).map(([opt, v]) => {
          const pct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
          return (
            <div key={opt}>
              <div className="clay-result-row">
                <span className="clay-result-name">{opt}</span>
                <span className="clay-result-stat">{v} vote{v > 1 ? 's' : ''} — {pct}%</span>
              </div>
              <div className="clay-progress-track clay-progress-track--lg">
                <div
                  className={`clay-progress-fill ${opt === winner?.[0] ? '' : 'clay-progress-fill--dim'}`}
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
