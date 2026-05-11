import { useNavigate } from 'react-router-dom'
import { useCommissionerState, useCounterState, useOpenVoting, useCloseVoting } from '../api'
import { useElectionStore } from '../store'
import { useEffect, useState, useRef } from 'react'
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

export default function Dashboard() {
  const navigate = useNavigate()
  const { cards, total, title } = useElectionStore()
  const { data: commState } = useCommissionerState()
  const { data: counterState } = useCounterState()
  const openVoting  = useOpenVoting()
  const closeVoting = useCloseVoting()
  const [msg, setMsg] = useState(null)
  const [logs, setLogs] = useState([])
  const logRef = useRef(null)

  useEffect(() => {
    if (cards.length === 0) navigate('/create', { replace: true })
  }, [cards.length, navigate])

  useEffect(() => {
    if (!commState) return
    const audit = commState.audit || []
    if (audit.length > 0) {
      setLogs(prev => {
        const lastTime = prev.length > 0 ? prev[prev.length - 1]?.time : null
        const newEntries = audit.filter(l => l.time !== lastTime)
        return newEntries.length === 0 ? prev : [...prev, ...newEntries]
      })
    }
  }, [commState])

  useEffect(() => {
    if (!commState?.phase) return
    const labels = { registration: 'Inscription', voting: 'Vote ouvert', done: 'Terminé', setup: 'Configuration' }
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg: `Phase → ${labels[commState.phase] || commState.phase}` }])
  }, [commState?.phase])

  const prevVotedRef = useRef(0)
  useEffect(() => {
    if (!commState) return
    const voted = commState.voted_count || 0
    if (voted > prevVotedRef.current) {
      setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg: `Bulletin reçu (${voted}/${commState.voter_count || total})` }])
    }
    prevVotedRef.current = voted
  }, [commState?.voted_count])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [logs])

  const voted      = commState?.voted_count || 0
  const voterTotal = commState?.voter_count || total
  const phase      = commState?.phase || 'registration'
  const results    = counterState?.results || {}
  const isDone     = counterState?.phase === 'done'
  const pct        = voterTotal > 0 ? Math.round((voted / voterTotal) * 100) : 0

  const handleOpen = async () => {
    try {
      await openVoting.mutateAsync()
      setMsg({ type: 'success', text: 'Le vote est maintenant ouvert !' })
    } catch (e) { setMsg({ type: 'error', text: e.message }) }
  }

  const handleClose = async () => {
    if (!confirm('Clôturer le scrutin et lancer le dépouillement ?')) return
    try {
      await closeVoting.mutateAsync()
      setMsg({ type: 'success', text: 'Scrutin clôturé et dépouillé.' })
    } catch (e) { setMsg({ type: 'error', text: e.message }) }
  }

  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const winner = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  if (cards.length === 0) return null

  return (
    <div className="clay-page-inner clay-page-inner--wide">

      {/* Header */}
      <div className="clay-page-header">
        <p className="clay-label">Tableau de bord</p>
        <h2 className="clay-page-title">{title || 'Scrutin'}</h2>
      </div>

      {/* Live pulse bar */}
      <div className="clay-live-bar">
        <div className="clay-live-left">
          <span className={`clay-dot ${phase === 'voting' ? 'bg-[#3D7A4E] animate-pulse' : 'bg-[#BFB9AF]'}`} />
          <span className="clay-live-label">Bulletins reçus</span>
        </div>
        <span className="clay-live-count">{voted} / {voterTotal}</span>
      </div>

      <div className="clay-dash-grid">

        {/* ── Left: voter cards ── */}
        <div>
          <div className="clay-section-toprow">
            <p className="clay-label">Cartes électeurs</p>
            <span className="clay-badge">{total} carte{total > 1 ? 's' : ''}</span>
          </div>
          <p className="clay-section-sub mb-4">
            Les codes <strong className="clay-strong-blue">N1</strong> et <strong className="clay-strong-amber">N2</strong> sont envoyés par email. N1 reste visible ici pour vérification.
          </p>
          <div className="clay-voter-cards-grid">
            {cards.map(card => {
              const initials = card.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
              return (
                <div key={card.name} className="clay-voter-card">
                  <div className="clay-voter-card-bar" />
                  <div className="clay-voter-card-head">
                    <div className="clay-voter-avatar">{initials}</div>
                    <div className="clay-voter-info">
                      <span className="clay-voter-name">{card.name}</span>
                      <span className="clay-voter-email">{card.email}</span>
                    </div>
                    <span className={`clay-email-badge ${card.email_sent ? 'clay-email-badge--ok' : 'clay-email-badge--fail'}`}>
                      {card.email_sent ? '✓ Email' : '✗ Email'}
                    </span>
                  </div>
                  <div className="clay-voter-code-row">
                    <div>
                      <div className="clay-code-label">N1 — Identification</div>
                      <div className="clay-code-value">{card.N1_fmt}</div>
                    </div>
                    <CopyBtn value={card.N1_fmt} />
                  </div>
                  <div>
                    <div className="clay-code-label">TTH(N2)</div>
                    <div className="clay-code-hash">{card.tth_N2}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── Right: controls ── */}
        <div className="clay-controls-col">

          {/* Phase & buttons */}
          <div className="clay-card">
            <p className="clay-label mb-4">Contrôles</p>
            <div className="clay-phase-row">
              <span className={`clay-dot ${isDone ? 'bg-[#BFB9AF]' : phase === 'voting' ? 'bg-[#3D7A4E] animate-pulse' : 'bg-[#B8860B]'}`} />
              <span className="clay-phase-label">
                {isDone ? 'Terminé' : phase === 'voting' ? 'Vote ouvert' : 'Inscription'}
              </span>
            </div>
            <div className="clay-btn-col">
              <Btn slug="ouvrir"  alt="Ouvrir le vote"         onClick={handleOpen}  disabled={phase !== 'registration' || openVoting.isPending} />
              <Btn slug="cloture" alt="Clôturer & dépouiller"  onClick={handleClose} disabled={phase !== 'voting'        || closeVoting.isPending} />
            </div>
            {msg && <Alert type={msg.type} className="mt-4">{msg.text}</Alert>}
          </div>

          {/* Participation */}
          <div className="clay-card">
            <p className="clay-label mb-4">Participation</p>
            {phase === 'voting' || isDone ? (
              <div>
                <div className="clay-progress-header">
                  <span className="clay-progress-label">Participation</span>
                  <span className="clay-progress-value">{voted} / {voterTotal} — {pct}%</span>
                </div>
                <div className="clay-progress-track">
                  <div className="clay-progress-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
            ) : (
              <p className="clay-muted">En attente…</p>
            )}
          </div>

          {/* Results */}
          {isDone && (
            <div className="clay-card clay-card--result">
              <p className="clay-label clay-label--green mb-4">Résultats</p>
              {winner && (
                <div className="clay-winner-box">
                  <div className="clay-winner-eyebrow">◈ Vainqueur</div>
                  <div className="clay-winner-name">{winner[0]}</div>
                  <div className="clay-winner-sub">{winner[1]} vote{winner[1] > 1 ? 's' : ''} · {totalValid} total</div>
                </div>
              )}
              <div className="clay-results-list">
                {Object.entries(results).sort((a, b) => b[1] - a[1]).map(([opt, v]) => {
                  const optPct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
                  return (
                    <div key={opt}>
                      <div className="clay-result-row">
                        <span className="clay-result-name">{opt}</span>
                        <span className="clay-result-stat">{v} — {optPct}%</span>
                      </div>
                      <div className="clay-progress-track">
                        <div className={`clay-progress-fill ${opt === winner?.[0] ? '' : 'clay-progress-fill--dim'}`}
                          style={{ width: `${optPct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Activity log */}
          <div className="clay-card">
            <p className="clay-label mb-3">Activité en direct</p>
            <div ref={logRef} className="clay-log">
              {logs.length === 0 ? (
                <p className="clay-muted">En attente d'activité…</p>
              ) : (
                logs.map((l, i) => (
                  <div key={i} className="clay-log-row">
                    <span className="clay-log-time">{l.time}</span>
                    <span className="clay-log-msg">{l.msg}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

function CopyBtn({ value }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value.replace(/\s/g, ''))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {}
  }
  return (
    <button onClick={handleCopy} className="clay-copy-btn" style={{ color: copied ? '#3D7A4E' : undefined }}>
      {copied ? '✓' : '⧉'}
    </button>
  )
}
