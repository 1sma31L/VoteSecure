import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCommissionerState, useCryptoParams, useValidateN1, useSignBlind, useSubmitVote, useCounterState } from '../api'
import { prepareBlindSignature, unblindSignature, verifySignature, encryptChoice, formatCode, encryptVote } from '../crypto'
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

export default function Voter() {
  const navigate = useNavigate()
  const [loaded, setLoaded]               = useState(false)
  const [electionTitle, setElectionTitle] = useState('')
  const [candidates, setCandidates]       = useState([])
  const [cryptoKeys, setCryptoKeys]       = useState(null)
  const [loadError, setLoadError]         = useState(null)

  const [step, setStep]                   = useState(1)
  const [n1Value, setN1Value]             = useState('')
  const [n2Value, setN2Value]             = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [selectedIndex, setSelectedIndex]   = useState(null)
  const [verifiedN1, setVerifiedN1]         = useState(null)
  const [alert, setAlert]                   = useState(null)
  const [busy, setBusy]                     = useState(false)
  const [busyLabel, setBusyLabel]           = useState('')
  const [trace, setTrace]                   = useState(null)
  const [receiptId, setReceiptId]           = useState('')
  const [showTrace, setShowTrace]           = useState(false)

  const { data: commState } = useCommissionerState()
  const { data: counterState } = useCounterState()
  const validateN1 = useValidateN1()
  const signBlind  = useSignBlind()
  const submitVote = useSubmitVote()

  useEffect(() => {
    if (loaded || !commState) return
    if (commState.phase === 'voting') handleLoad()
  }, [commState, loaded])

  const handleLoad = async () => {
    setLoadError(null)
    try {
      if (!commState) { setLoadError('Impossible de contacter le commissaire.'); return }
      if (commState.phase === 'setup')        { setLoadError('Aucun scrutin actif.'); return }
      if (commState.phase === 'registration') { setLoadError('Le vote n\'est pas encore ouvert.'); return }
      if (commState.phase === 'done')         { navigate('/results'); return }

      const cpRes = await fetch('/api/crypto_params').then(r => r.json())
      if (!cpRes.admin || !cpRes.counter) {
        setLoadError('Clés RSA non disponibles. Initialisez l\'administrateur et le décompteur.')
        return
      }
      setCryptoKeys({ admin_e: cpRes.admin.e, admin_N: cpRes.admin.N, counter_e: cpRes.counter.e, counter_N: cpRes.counter.N })
      setElectionTitle(commState.election_title || 'Scrutin actif')
      setCandidates(commState.candidates || [])
      setLoaded(true)
    } catch (e) { setLoadError(e.message) }
  }

  const handleVerifyN1 = async () => {
    const N1 = n1Value.replace(/\s/g, '').toUpperCase()
    if (N1.length !== 12) { setAlert({ type: 'error', text: 'Le code N1 doit faire 12 caractères' }); return }
    setAlert(null); setBusy(true); setBusyLabel('Vérification…')
    try {
      const result = await validateN1.mutateAsync({ N1 })
      if (!result.valid) { setAlert({ type: 'error', text: 'N1 Code not valid or already used' }); return }
      setVerifiedN1(N1); setStep(2)
    } catch (e) {
      setAlert({ type: 'error', text: `Verification error ${e.message}` })
    } finally { setBusy(false); setBusyLabel('') }
  }

  const handleSubmitVote = async () => {
    const N2 = n2Value.replace(/\s/g, '').toUpperCase()
    if (selectedOption == null) { setAlert({ type: 'error', text: 'Sélectionnez un candidat' }); return }
    if (N2.length !== 12)       { setAlert({ type: 'error', text: 'Le code N2 doit faire 12 caractères' }); return }
    if (!cryptoKeys)            { setAlert({ type: 'error', text: 'Paramètres crypto manquants. Rechargez le scrutin.' }); return }
    if (!verifiedN1)            { setAlert({ type: 'error', text: 'Commencez par vérifier N1' }); return }

    setAlert(null); setBusy(true)
    try {
      const admin_e   = BigInt(cryptoKeys.admin_e)
      const admin_N   = BigInt(cryptoKeys.admin_N)
      const counter_e = BigInt(cryptoKeys.counter_e)
      const counter_N = BigInt(cryptoKeys.counter_N)

      setBusyLabel('Préparation…')
      const { m_int, k, m_masked } = await prepareBlindSignature(selectedIndex, N2, admin_e, admin_N)

      setBusyLabel('Signature aveugle…')
      const blindData = await signBlind.mutateAsync({ N1: verifiedN1, m_masked: m_masked.toString() })
      if (blindData.error) throw new Error(blindData.error)

      const s_blind   = BigInt(blindData.s_blind)
      const signature = unblindSignature(s_blind, k, admin_N)
      const verify_ok = verifySignature(signature, admin_e, admin_N, m_int)
      if (!verify_ok) throw new Error('Erreur de vérification de la signature — recommencez')

      const encrypted = encryptVote(selectedIndex, N2, counter_e, counter_N)

      setBusyLabel('Transmission…')
      const subData = await submitVote.mutateAsync({
        N1: verifiedN1, encrypted_ballot: encrypted.toString(),
        choice_index: selectedIndex, signature: signature.toString(), m_int: m_int.toString(),
      })
      if (subData.error) throw new Error(subData.error)

      setStep(3); setReceiptId(subData.receipt_id || '')
      setTrace({
        choice: selectedOption, choiceIdx: selectedIndex,
        m_int: m_int.toString(), k: k.toString(), m_masked: m_masked.toString(),
        s_blind: s_blind.toString(), signature: signature.toString(), encrypted: encrypted.toString(),
        verify_ok, verify_val: modPow(signature, admin_e, admin_N).toString(),
      })
    } catch (e) {
      setAlert({ type: 'error', text: e.message })
    } finally { setBusy(false); setBusyLabel('') }
  }

  // ── Not loaded ─────────────────────────────────────────────────────────────
  if (!loaded) {
    return (
      <div className="clay-page-inner clay-center">
        <div className="clay-page-header">
          <p className="clay-label">Électeur</p>
          <h2 className="clay-page-title">Espace de vote</h2>
        </div>
        <div className="clay-card" style={{ maxWidth: 420, width: '100%' }}>
          {loadError ? (
            <Alert type="error" className="mb-4">{loadError}</Alert>
          ) : (
            <p className="clay-muted mb-4">Connexion au scrutin en cours…</p>
          )}
          <div className="flex justify-center">
            <Btn slug="retour" alt="Retour à l'accueil" onClick={() => navigate('/')} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="clay-page-inner">
      <div className="clay-page-header">
        <p className="clay-label">Électeur</p>
        <h2 className="clay-page-title">{electionTitle}</h2>
      </div>

      {/* Step indicator */}
      <div className="clay-step-indicator">
        {[1, 2, 3].map(n => (
          <div key={n} className="clay-step-item">
            <div className={`clay-step-dot ${step >= n ? 'clay-step-dot--active' : ''}`}>{n}</div>
            <span className="clay-step-label">{['Identification', 'Vote', 'Confirmation'][n - 1]}</span>
          </div>
        ))}
      </div>

      {/* ── Step 1: N1 ──────────────────────────────────────────────────── */}
      {step === 1 && (
        <div className="clay-card">
          <p className="clay-label mb-4">Code d'identification N1</p>
          <p className="clay-page-sub mb-4">Entrez votre code N1 reçu par email. Il vous identifie sans révéler votre vote.</p>
          <div className="clay-field mb-4">
            <label className="clay-field-label">Code N1</label>
            <input
              type="text"
              value={n1Value}
              onChange={e => setN1Value(formatCode(e.target.value))}
              placeholder="XXXX XXXX XXXX"
              maxLength={14}
              className="clay-input clay-input--mono clay-input--center"
            />
          </div>
          {alert && <Alert type={alert.type} className="mb-4">{alert.text}</Alert>}
          {busy ? (
            <div className="clay-busy-state"><span className="clay-spinner" /><span className="clay-busy-label">{busyLabel}</span></div>
          ) : (
            <div className="flex justify-center">
              <Btn slug="verifier" alt="Vérifier mon identité" onClick={handleVerifyN1} />
            </div>
          )}
        </div>
      )}

      {/* ── Step 2: Vote + N2 ───────────────────────────────────────────── */}
      {step === 2 && (
        <>
          <Alert type="success" className="mb-4">Votre droit de vote est confirmé.</Alert>

          {/* Candidate grid */}
          <div className="clay-card mb-4">
            <p className="clay-label mb-3">Votre choix</p>
            <div className="clay-candidates-grid">
              {candidates.map((opt, idx) => (
                <button
                  key={idx}
                  onClick={() => { setSelectedOption(opt); setSelectedIndex(idx) }}
                  className={`clay-candidate-btn ${selectedIndex === idx ? 'clay-candidate-btn--selected' : ''}`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* N2 */}
          <div className="clay-card">
            <p className="clay-label mb-2">Code d'authentification N2</p>
            <p className="clay-page-sub mb-4">Ce code n'est jamais transmis en clair — il est haché côté navigateur.</p>
            <div className="clay-field mb-4">
              <label className="clay-field-label">Code N2</label>
              <input
                type="text"
                value={n2Value}
                onChange={e => setN2Value(formatCode(e.target.value))}
                placeholder="XXXX XXXX XXXX"
                maxLength={14}
                className="clay-input clay-input--mono clay-input--center"
              />
            </div>
            {alert && <Alert type={alert.type} className="mb-4">{alert.text}</Alert>}
            {busy ? (
              <div className="clay-busy-state"><span className="clay-spinner" /><span className="clay-busy-label">{busyLabel}</span></div>
            ) : (
              <div className="flex justify-center">
                <Btn slug="signer" alt="Signer & soumettre mon bulletin" onClick={handleSubmitVote} />
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Step 3: Confirmation ────────────────────────────────────────── */}
      {step === 3 && (
        <>
          <div className="clay-success-block">
            <div className="clay-success-icon">✅</div>
            <h2 className="clay-page-title">Bulletin enregistré</h2>
            <p className="clay-page-sub">Votre vote a été signé à l'aveugle, chiffré et transmis à l'anonymiseur.</p>
            {receiptId && <div className="clay-receipt">Reçu : {receiptId}</div>}
          </div>

          {trace && (
            <div className="clay-card mb-4">
              <div className="clay-trace-header">
                <p className="clay-label">Trace cryptographique</p>
                <button onClick={() => setShowTrace(!showTrace)} className="clay-trace-toggle">
                  {showTrace ? 'Masquer' : 'Afficher'}
                </button>
              </div>
              {showTrace && (
                <div className="clay-trace-body">
                  <div>Candidat    = <span className="clay-trace-val">{trace.choice} (index {trace.choiceIdx})</span></div>
                  <div>m_int       = <span className="clay-trace-val">{trace.m_int}</span></div>
                  <div>k (aveugle) = <span className="clay-trace-val">{trace.k}</span></div>
                  <div>m_masked    = <span className="clay-trace-val">{trace.m_masked}</span></div>
                  <div>s_blind     = <span className="clay-trace-val">{trace.s_blind}</span></div>
                  <div>signature   = <span className="clay-trace-val">{trace.signature}</span></div>
                  <div>E(vote)     = <span className="clay-trace-val">{trace.encrypted}</span></div>
                  <div className={trace.verify_ok ? 'clay-trace-ok' : 'clay-trace-err'}>
                    ◈ Vérif. s^e mod N = {trace.verify_val} — {trace.verify_ok ? '✓ VALIDE' : '✗ ERREUR'}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="clay-card clay-center">
            <p className="clay-page-sub mb-4">Le scrutin est toujours en cours. Vérifiez les résultats ou attendez la clôture.</p>
            <CheckResultsButton />
          </div>
        </>
      )}
    </div>
  )
}

function CheckResultsButton() {
  const { data: counterState, refetch, isFetching } = useCounterState()
  const [checked, setChecked] = useState(false)

  const handleCheck = async () => {
    await refetch()
    setChecked(true)
  }

  const results    = counterState?.results || {}
  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const isDone     = counterState?.phase === 'done'
  const winner     = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  return (
    <div>
      <button
        onClick={handleCheck}
        disabled={isFetching}
        className="clay-img-btn"
      >
        <img src="/assets/buttons/btn-resultats.png" alt="Vérifier les résultats"
          className="block h-auto pointer-events-none select-none" draggable={false} />
      </button>
      {checked && (
        <div className="mt-4 text-left">
          {isDone ? (
            <div className="clay-results-list">
              {winner && (
                <div className="clay-winner-box mb-3">
                  <div className="clay-winner-eyebrow">◈ Vainqueur</div>
                  <div className="clay-winner-name">{winner[0]}</div>
                  <div className="clay-winner-sub">{winner[1]} — {totalValid} total</div>
                </div>
              )}
              {Object.entries(results).sort((a, b) => b[1] - a[1]).map(([opt, v]) => {
                const pct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
                return (
                  <div key={opt}>
                    <div className="clay-result-row">
                      <span className="clay-result-name">{opt}</span>
                      <span className="clay-result-stat">{v} — {pct}%</span>
                    </div>
                    <div className="clay-progress-track">
                      <div className={`clay-progress-fill ${opt === winner?.[0] ? '' : 'clay-progress-fill--dim'}`}
                        style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="clay-muted mt-2">Le scrutin n'est pas encore clôturé. Réessayez.</p>
          )}
        </div>
      )}
    </div>
  )
}

function modPow(base, exp, mod) {
  ;[base, exp, mod] = [BigInt(base), BigInt(exp), BigInt(mod)]
  let result = 1n; base %= mod
  while (exp > 0n) {
    if (exp & 1n) result = (result * base) % mod
    exp >>= 1n; base = (base * base) % mod
  }
  return result
}
