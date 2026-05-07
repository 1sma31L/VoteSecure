import { useNavigate } from 'react-router-dom'
import { useCommissionerState, useCounterState, useOpenVoting, useCloseVoting } from '../api'
import { useElectionStore } from '../store'
import { useEffect, useState, useRef } from 'react'
import Alert from '../components/Alert'

export default function Dashboard() {
  const navigate = useNavigate()
  const { cards, total, title } = useElectionStore()
  const { data: commState } = useCommissionerState()
  const { data: counterState } = useCounterState()
  const openVoting = useOpenVoting()
  const closeVoting = useCloseVoting()
  const [msg, setMsg] = useState(null)
  const [logs, setLogs] = useState([])
  const logRef = useRef(null)

  // If no cards, redirect to create
  useEffect(() => {
    if (cards.length === 0) navigate('/create', { replace: true })
  }, [cards.length, navigate])

  // Build activity logs from commissioner state
  useEffect(() => {
    if (!commState) return
    const audit = commState.audit || []
    if (audit.length > 0) {
      setLogs((prev) => {
        const lastTime = prev.length > 0 ? prev[prev.length - 1]?.time : null
        const newEntries = audit.filter((l) => l.time !== lastTime)
        if (newEntries.length === 0) return prev
        return [...prev, ...newEntries]
      })
    }
  }, [commState])

  // Log phase changes
  useEffect(() => {
    if (!commState?.phase) return
    const phaseLabels = { registration: 'Inscription', voting: 'Vote ouvert', done: 'Terminé', setup: 'Configuration' }
    const label = phaseLabels[commState.phase] || commState.phase
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg: `Phase → ${label}` }])
  }, [commState?.phase])

  // Log vote count changes
  const prevVotedRef = useRef(0)
  useEffect(() => {
    if (!commState) return
    const voted = commState.voted_count || 0
    if (voted > prevVotedRef.current) {
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg: `Bulletin reçu (${voted}/${commState.voter_count || total})` }])
    }
    prevVotedRef.current = voted
  }, [commState?.voted_count])

  // Auto-scroll logs
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [logs])

  const voted = commState?.voted_count || 0
  const voterTotal = commState?.voter_count || total
  const phase = commState?.phase || 'registration'
  const counterPhase = counterState?.phase
  const results = counterState?.results || {}
  const isDone = counterPhase === 'done'

  const pct = voterTotal > 0 ? Math.round((voted / voterTotal) * 100) : 0

  const handleOpen = async () => {
    try {
      await openVoting.mutateAsync()
      setMsg({ type: 'success', text: 'Le vote est maintenant ouvert !' })
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  const handleClose = async () => {
    if (!confirm('Clôturer le scrutin et lancer le dépouillement ?')) return
    try {
      await closeVoting.mutateAsync()
      setMsg({ type: 'success', text: 'Scrutin clôturé et dépouillé.' })
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const winner = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  if (cards.length === 0) return null

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Title */}
      <div className="mb-6">
        <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-[0.2em] mb-1 font-mono">Tableau de bord</p>
        <h2 className="font-display text-2xl font-black text-white tracking-tight">{title || 'Scrutin'}</h2>
      </div>

      {/* Live bar */}
      <div className="bg-surface-2 border border-neon-blue/20 rounded-2xl px-5 py-4 flex items-center justify-between mb-6">
        <div className="flex items-center gap-3 text-sm font-semibold text-slate-300">
          <span className={`w-2.5 h-2.5 rounded-full ${phase === 'voting' ? 'bg-neon-green animate-pulse' : 'bg-slate-600'}`} />
          Bulletins reçus
        </div>
        <div className="font-mono font-bold text-neon-blue">
          {voted} / {voterTotal}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: voter cards */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest font-mono">Cartes électeurs</p>
            <span className="text-xs font-mono font-bold text-neon-blue bg-neon-blue/10 border border-neon-blue/20 rounded-full px-2.5 py-0.5">
              {total} carte{total > 1 ? 's' : ''}
            </span>
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Les codes <span className="text-neon-cyan font-semibold">N1</span> et <span className="text-neon-orange font-semibold">N2</span> sont envoyés par email à chaque électeur. N1 reste visible ici pour vérification.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {cards.map((card) => {
              const initials = card.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
              return (
                <div key={card.name} className="relative bg-surface-2 border border-surface-5 rounded-2xl p-5 overflow-hidden">
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-neon-blue to-neon-cyan" />
                  <div className="flex items-center gap-2.5 mb-3">
                    <div className="w-7 h-7 bg-neon-blue/10 rounded-full flex items-center justify-center text-[0.65rem] font-extrabold text-neon-blue">
                      {initials}
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="font-display font-extrabold text-sm text-white block truncate">{card.name}</span>
                      <span className="text-[0.6rem] text-slate-500 font-mono truncate block">{card.email}</span>
                    </div>
                    {card.email_sent ? (
                      <span className="text-[0.55rem] font-bold text-neon-green bg-neon-green/10 border border-neon-green/20 rounded-full px-2 py-0.5 shrink-0">✓ Email</span>
                    ) : (
                      <span className="text-[0.55rem] font-bold text-neon-orange bg-neon-orange/10 border border-neon-orange/20 rounded-full px-2 py-0.5 shrink-0">✗ Email</span>
                    )}
                  </div>
                  <div className="mb-2">
                    <div className="flex items-center justify-between">
                      <div className="text-[0.55rem] font-bold text-neon-cyan/60 uppercase tracking-widest">N1 — Identification</div>
                      <CopyBtn value={card.N1_fmt} label="N1" />
                    </div>
                    <div className="font-mono text-sm font-semibold text-white tracking-widest">{card.N1_fmt}</div>
                  </div>
                  <div>
                    <div className="text-[0.55rem] font-bold text-slate-500 uppercase tracking-widest">TTH(N2)</div>
                    <div className="font-mono text-[0.55rem] text-slate-500 break-all">{card.tth_N2}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: controls */}
        <div className="space-y-4">
          {/* Phase + controls */}
          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-5">
            <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-4 font-mono">Contrôles</p>
            <div className="flex items-center gap-2.5 mb-5">
              <span className={`w-3 h-3 rounded-full ${
                isDone ? 'bg-slate-500' : phase === 'voting' ? 'bg-neon-green animate-pulse' : 'bg-neon-orange'
              }`} />
              <span className="font-display font-bold text-white">
                {isDone ? 'Terminé' : phase === 'voting' ? 'Vote ouvert' : 'Inscription'}
              </span>
            </div>
            <button
              onClick={handleOpen}
              disabled={phase !== 'registration' || openVoting.isPending}
              className="w-full bg-neon-green/20 border border-neon-green/30 text-neon-green font-bold px-5 py-3 rounded-xl hover:bg-neon-green/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors mb-3"
            >
              ▶ Ouvrir le vote
            </button>
            <button
              onClick={handleClose}
              disabled={phase !== 'voting' || closeVoting.isPending}
              className="w-full bg-neon-pink/20 border border-neon-pink/30 text-neon-pink font-bold px-5 py-3 rounded-xl hover:bg-neon-pink/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ⏹ Clôturer & dépouiller
            </button>
            {msg && <Alert type={msg.type} className="mt-4">{msg.text}</Alert>}
          </div>

          {/* Participation */}
          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-5">
            <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-4 font-mono">Participation</p>
            {phase === 'voting' || isDone ? (
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-slate-400">Participation</span>
                  <span className="font-bold text-white">{voted} / {voterTotal} — {pct}%</span>
                </div>
                <div className="h-2 bg-surface-4 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-neon-blue to-neon-cyan rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">En attente…</p>
            )}
          </div>

          {/* Results (when done) */}
          {isDone && (
            <div className="bg-surface-2 border border-neon-green/20 rounded-2xl p-5">
              <p className="text-[0.7rem] font-bold text-neon-green uppercase tracking-widest mb-4 font-mono">Résultats</p>
              {winner && (
                <div className="bg-gradient-to-br from-brand-900 to-brand-700 rounded-2xl p-6 text-center mb-4 shadow-lg shadow-brand-900/50">
                  <div className="text-[0.6rem] font-bold tracking-[0.15em] uppercase text-white/40 mb-2 font-mono">◈ Vainqueur</div>
                  <div className="font-display text-2xl font-black text-white">{winner[0]}</div>
                  <div className="text-white/50 text-sm font-mono mt-1">{winner[1]} vote{winner[1] > 1 ? 's' : ''} · {totalValid} total</div>
                </div>
              )}
              <div className="space-y-3">
                {Object.entries(results).sort((a, b) => b[1] - a[1]).map(([opt, v]) => {
                  const optPct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
                  return (
                    <div key={opt}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-bold text-white">{opt}</span>
                        <span className="text-slate-500 font-mono text-xs">{v} — {optPct}%</span>
                      </div>
                      <div className="h-2.5 bg-surface-4 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-1000 ${opt === winner?.[0] ? 'bg-gradient-to-r from-neon-blue to-neon-cyan' : 'bg-surface-5'}`}
                          style={{ width: `${optPct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Activity log */}
          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-5">
            <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-3 font-mono">Activité en direct</p>
            <div ref={logRef} className="font-mono text-[0.65rem] text-slate-500 leading-relaxed max-h-48 overflow-y-auto space-y-1">
              {logs.length === 0 ? (
                <p className="text-slate-600">En attente d'activité…</p>
              ) : (
                logs.map((l, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-slate-600 shrink-0">{l.time}</span>
                    <span>{l.msg}</span>
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

function CopyBtn({ value, label }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value.replace(/\s/g, ''))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {}
  }

  return (
    <button
      onClick={handleCopy}
      className="text-[0.55rem] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded transition-colors shrink-0"
      style={{ color: copied ? '#51cf66' : undefined }}
    >
      {copied ? '✓' : '⧉'}
    </button>
  )
}
