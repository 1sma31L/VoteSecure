import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCommissionerState, useCryptoParams, useValidateN1, useSignBlind, useSubmitVote, useCounterState } from '../api'
import { prepareBlindSignature, unblindSignature, verifySignature, encryptChoice, formatCode } from '../crypto'
import Alert from '../components/Alert'

export default function Voter() {
  const navigate = useNavigate()
  const [loaded, setLoaded] = useState(false)
  const [electionTitle, setElectionTitle] = useState('')
  const [candidates, setCandidates] = useState([])
  const [cryptoKeys, setCryptoKeys] = useState(null)
  const [loadError, setLoadError] = useState(null)

  // Step state
  const [step, setStep] = useState(1) // 1=N1, 2=vote, 3=confirm
  const [n1Value, setN1Value] = useState('')
  const [n2Value, setN2Value] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [selectedIndex, setSelectedIndex] = useState(null)
  const [verifiedN1, setVerifiedN1] = useState(null)
  const [alert, setAlert] = useState(null)
  const [busy, setBusy] = useState(false)
  const [busyLabel, setBusyLabel] = useState('')
  const [trace, setTrace] = useState(null)
  const [receiptId, setReceiptId] = useState('')
  const [showTrace, setShowTrace] = useState(false)

  const { data: commState } = useCommissionerState()
  const { data: counterState } = useCounterState()
  const validateN1 = useValidateN1()
  const signBlind = useSignBlind()
  const submitVote = useSubmitVote()

  // Auto-load if voting is open
  useEffect(() => {
    if (loaded || !commState) return
    if (commState.phase === 'voting') {
      handleLoad()
    }
  }, [commState, loaded])

  const handleLoad = async () => {
    setLoadError(null)
    try {
      if (!commState) {
        setLoadError('Impossible de contacter le commissaire.')
        return
      }
      if (commState.phase === 'setup') {
        setLoadError('Aucun scrutin actif.')
        return
      }
      if (commState.phase === 'registration') {
        setLoadError('Le vote n\'est pas encore ouvert.')
        return
      }
      if (commState.phase === 'done') {
        // Show results directly
        navigate('/results')
        return
      }

      // Fetch crypto params
      const cpRes = await fetch('/api/crypto_params').then((r) => r.json())
      if (!cpRes.admin || !cpRes.counter) {
        setLoadError('Clés RSA non disponibles. Initialisez l\'administrateur et le décompteur.')
        return
      }

      setCryptoKeys({
        admin_e: cpRes.admin.e,
        admin_N: cpRes.admin.N,
        counter_e: cpRes.counter.e,
        counter_N: cpRes.counter.N,
      })
      setElectionTitle(commState.election_title || 'Scrutin actif')
      setCandidates(commState.candidates || [])
      setLoaded(true)
    } catch (e) {
      setLoadError(e.message)
    }
  }

  const handleVerifyN1 = async () => {
    const N1 = n1Value.replace(/\s/g, '').toUpperCase()
    if (N1.length !== 12) {
      setAlert({ type: 'error', text: 'Le code N1 doit faire 12 caractères' })
      return
    }
    setAlert(null)

    try {
      // Optional N1 check
      try { await validateN1.mutateAsync({ N1 }) } catch {}

      setVerifiedN1(N1)
      setStep(2)
    } catch (e) {
      setAlert({ type: 'error', text: e.message })
    }
  }

  const handleSubmitVote = async () => {
    const N2 = n2Value.replace(/\s/g, '').toUpperCase()
    if (selectedOption == null) {
      setAlert({ type: 'error', text: 'Sélectionnez un candidat' })
      return
    }
    if (N2.length !== 12) {
      setAlert({ type: 'error', text: 'Le code N2 doit faire 12 caractères' })
      return
    }
    if (!cryptoKeys) {
      setAlert({ type: 'error', text: 'Paramètres crypto manquants. Rechargez le scrutin.' })
      return
    }
    if (!verifiedN1) {
      setAlert({ type: 'error', text: 'Commencez par vérifier N1' })
      return
    }

    setAlert(null)
    setBusy(true)

    try {
      const admin_e = BigInt(cryptoKeys.admin_e)
      const admin_N = BigInt(cryptoKeys.admin_N)
      const counter_e = BigInt(cryptoKeys.counter_e)
      const counter_N = BigInt(cryptoKeys.counter_N)

      // Step 1: Prepare blind signature
      setBusyLabel('Préparation…')
      const { m_int, k, m_masked } = await prepareBlindSignature(selectedIndex, N2, admin_e, admin_N)

      // Step 2: Get blind signature from admin
      setBusyLabel('Signature aveugle…')
      const blindData = await signBlind.mutateAsync({ N1: verifiedN1, m_masked: m_masked.toString() })
      if (blindData.error) throw new Error(blindData.error)

      const s_blind = BigInt(blindData.s_blind)
      const signature = unblindSignature(s_blind, k, admin_N)
      const verify_ok = verifySignature(signature, admin_e, admin_N, m_int)
      if (!verify_ok) throw new Error('Erreur de vérification de la signature — recommencez')

      // Step 3: Encrypt choice
      const encrypted = encryptChoice(selectedIndex, counter_e, counter_N)

      // Step 4: Submit
      setBusyLabel('Transmission…')
      const subData = await submitVote.mutateAsync({
        N1: verifiedN1,
        encrypted_ballot: encrypted.toString(),
        choice_index: selectedIndex,
        signature: signature.toString(),
        m_int: m_int.toString(),
      })
      if (subData.error) throw new Error(subData.error)

      // Success
      setStep(3)
      setReceiptId(subData.receipt_id || '')
      setTrace({
        choice: selectedOption,
        choiceIdx: selectedIndex,
        m_int: m_int.toString(),
        k: k.toString(),
        m_masked: m_masked.toString(),
        s_blind: s_blind.toString(),
        signature: signature.toString(),
        encrypted: encrypted.toString(),
        verify_ok,
        verify_val: modPow(signature, admin_e, admin_N).toString(),
      })
    } catch (e) {
      setAlert({ type: 'error', text: e.message })
    } finally {
      setBusy(false)
      setBusyLabel('')
    }
  }

  // Not loaded yet
  if (!loaded) {
    return (
      <div className="max-w-xl mx-auto px-6 py-12">
        <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6">
          <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-2 font-mono">Électeur</p>
          <p className="text-sm text-slate-400 mb-5">Chargez les paramètres du scrutin actif depuis le commissaire.</p>
          <button
            onClick={handleLoad}
            className="w-full bg-brand-600 text-white font-bold px-5 py-3 rounded-xl hover:bg-brand-500 transition-colors shadow-lg shadow-brand-600/20"
          >
            🔄 Charger le scrutin actif
          </button>
          {loadError && <Alert type="warning" className="mt-4">{loadError}</Alert>}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto px-6 py-10">
      {/* Step indicator */}
      <div className="flex items-center mb-8">
        {[
          { n: 1, label: 'Identification' },
          { n: 2, label: 'Vote' },
          { n: 3, label: 'Confirmation' },
        ].map((s, i) => (
          <div key={s.n} className="flex items-center flex-1">
            <div className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold font-mono shrink-0 transition-colors ${
                  step > s.n
                    ? 'bg-neon-green/20 text-neon-green border border-neon-green/30'
                    : step === s.n
                    ? 'bg-brand-600 text-white'
                    : 'bg-surface-3 text-slate-500 border border-surface-5'
                }`}
              >
                {step > s.n ? '✓' : s.n}
              </div>
              <span
                className={`text-xs font-bold uppercase tracking-wide ${
                  step > s.n ? 'text-neon-green' : step === s.n ? 'text-brand-300' : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
            </div>
            {i < 2 && <div className={`flex-1 h-0.5 mx-3 rounded ${step > s.n ? 'bg-neon-green/40' : 'bg-surface-5'}`} />}
          </div>
        ))}
      </div>

      <div className="font-display text-xl font-black text-white mb-6">{electionTitle}</div>

      {/* Step 1: N1 */}
      {step === 1 && (
        <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6">
          <p className="text-[0.7rem] font-bold text-neon-cyan uppercase tracking-widest mb-2 font-mono">Code d'identification N1</p>
          <p className="text-sm text-slate-400 mb-4">Entrez le code N1 figurant sur votre carte électeur.</p>
          <div className="mb-4">
            <label className="block text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-1.5 font-mono">Code N1</label>
            <input
              type="text"
              value={n1Value}
              onChange={(e) => setN1Value(formatCode(e.target.value))}
              placeholder="XXXX XXXX XXXX"
              maxLength={14}
              className="w-full bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 text-center font-mono text-sm tracking-widest text-white placeholder:text-slate-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all"
            />
          </div>
          {alert && <Alert type={alert.type} className="mb-4">{alert.text}</Alert>}
          <button
            onClick={handleVerifyN1}
            className="w-full bg-brand-600 text-white font-bold px-5 py-3 rounded-xl hover:bg-brand-500 transition-colors shadow-lg shadow-brand-600/20"
          >
            Vérifier mon identité →
          </button>
        </div>
      )}

      {/* Step 2: Vote + N2 */}
      {step === 2 && (
        <>
          <Alert type="success" className="mb-4">Votre droit de vote est confirmé.</Alert>

          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6 mb-4">
            <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-3 font-mono">Votre choix</p>
            <div className="grid grid-cols-2 gap-3">
              {candidates.map((opt, idx) => (
                <button
                  key={idx}
                  onClick={() => { setSelectedOption(opt); setSelectedIndex(idx) }}
                  className={`p-5 rounded-xl text-sm font-bold text-center transition-all ${
                    selectedIndex === idx
                      ? 'bg-neon-blue/15 border-2 border-neon-blue/40 text-white shadow-sm shadow-neon-blue/10'
                      : 'bg-surface-3 border-2 border-surface-5 text-slate-400 hover:border-brand-700/40 hover:text-white'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6">
            <p className="text-[0.7rem] font-bold text-neon-orange uppercase tracking-widest mb-2 font-mono">Code d'authentification N2</p>
            <p className="text-sm text-slate-400 mb-4">Ce code n'est jamais transmis en clair — il est haché côté navigateur.</p>
            <div className="mb-4">
              <label className="block text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-1.5 font-mono">Code N2</label>
              <input
                type="text"
                value={n2Value}
                onChange={(e) => setN2Value(formatCode(e.target.value))}
                placeholder="XXXX XXXX XXXX"
                maxLength={14}
                className="w-full bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 text-center font-mono text-sm tracking-widest text-white placeholder:text-slate-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all"
              />
            </div>
            {alert && <Alert type={alert.type} className="mb-4">{alert.text}</Alert>}
            <button
              onClick={handleSubmitVote}
              disabled={busy}
              className="w-full bg-brand-600 text-white font-display font-extrabold px-5 py-4 rounded-2xl text-base hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-lg shadow-brand-600/20"
            >
              {busy ? (
                <span className="inline-flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {busyLabel}
                </span>
              ) : (
                '🔏 Signer & soumettre mon bulletin'
              )}
            </button>
          </div>
        </>
      )}

      {/* Step 3: Confirmation */}
      {step === 3 && (
        <>
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-neon-green/10 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 border border-neon-green/20">✅</div>
            <h2 className="font-display text-2xl font-black text-white">Bulletin enregistré</h2>
            <p className="text-slate-400 mt-2">Votre vote a été signé à l'aveugle, chiffré et transmis à l'anonymiseur.</p>
            {receiptId && (
              <div className="mt-3 font-mono text-xs text-slate-500">Reçu : {receiptId}</div>
            )}
          </div>

          {trace && (
            <div className="bg-surface-2 border border-surface-5 rounded-2xl p-5 mb-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest font-mono">Trace cryptographique</p>
                <button
                  onClick={() => setShowTrace(!showTrace)}
                  className="text-xs font-semibold text-slate-500 hover:text-white transition-colors"
                >
                  {showTrace ? 'Masquer' : 'Afficher'}
                </button>
              </div>
              {showTrace && (
                <div className="bg-surface-0 rounded-xl p-4 font-mono text-[0.65rem] leading-loose text-slate-500 overflow-x-auto">
                  <div>Candidat{'          '}= <span className="text-neon-cyan">{trace.choice} (index {trace.choiceIdx})</span></div>
                  <div>m_int (hash){'      '}= <span className="text-neon-cyan">{trace.m_int}</span></div>
                  <div>k (aveugle){'       '}= <span className="text-neon-cyan">{trace.k}</span></div>
                  <div>m_masked{'           '}= <span className="text-neon-cyan">{trace.m_masked}</span></div>
                  <div>s_blind{'            '}= <span className="text-neon-cyan">{trace.s_blind}</span></div>
                  <div>signature{'          '}= <span className="text-neon-cyan">{trace.signature}</span></div>
                  <div>E(vote){'            '}= <span className="text-neon-cyan">{trace.encrypted}</span></div>
                  <div className={trace.verify_ok ? 'text-neon-green' : 'text-neon-pink'}>
                    ◈ Vérif. s^e mod N = {trace.verify_val} — {trace.verify_ok ? '✓ VALIDE' : '✗ ERREUR'}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="bg-surface-2 border border-surface-5 rounded-2xl p-5 text-center">
            <p className="text-sm text-slate-400 mb-4">
              Le scrutin est toujours en cours. Vérifiez les résultats ou attendez que l'organisateur clôture le vote.
            </p>
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
    const res = await refetch()
    setChecked(true)
  }

  const results = counterState?.results || {}
  const totalValid = Object.values(results).reduce((a, b) => a + b, 0)
  const isDone = counterState?.phase === 'done'
  const winner = Object.entries(results).sort((a, b) => b[1] - a[1])[0]

  return (
    <div>
      <button
        onClick={handleCheck}
        disabled={isFetching}
        className="bg-brand-600 text-white font-bold px-5 py-2.5 rounded-xl hover:bg-brand-500 disabled:opacity-40 transition-colors shadow-lg shadow-brand-600/20"
      >
        {isFetching ? 'Chargement…' : '↻ Vérifier les résultats'}
      </button>
      {checked && (
        <div className="mt-4 text-left">
          {isDone ? (
            <div className="space-y-3">
              {winner && (
                <div className="bg-gradient-to-br from-brand-900 to-brand-700 rounded-2xl p-5 text-center shadow-lg shadow-brand-900/50">
                  <div className="text-[0.6rem] font-bold tracking-[0.15em] uppercase text-white/40 mb-1 font-mono">◈ Vainqueur</div>
                  <div className="font-display text-xl font-black text-white">{winner[0]}</div>
                  <div className="text-white/50 text-xs font-mono mt-1">{winner[1]} — {totalValid} total</div>
                </div>
              )}
              {Object.entries(results).sort((a, b) => b[1] - a[1]).map(([opt, v]) => {
                const pct = totalValid > 0 ? Math.round((v / totalValid) * 100) : 0
                return (
                  <div key={opt}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-bold text-white">{opt}</span>
                      <span className="text-slate-500 font-mono text-xs">{v} — {pct}%</span>
                    </div>
                    <div className="h-2 bg-surface-4 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${opt === winner?.[0] ? 'bg-gradient-to-r from-neon-blue to-neon-cyan' : 'bg-surface-5'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-500 mt-2">Le scrutin n'est pas encore clôturé. Réessayez.</p>
          )}
        </div>
      )}
    </div>
  )
}

function modPow(base, exp, mod) {
  ;[base, exp, mod] = [BigInt(base), BigInt(exp), BigInt(mod)]
  let result = 1n
  base %= mod
  while (exp > 0n) {
    if (exp & 1n) result = (result * base) % mod
    exp >>= 1n
    base = (base * base) % mod
  }
  return result
}
