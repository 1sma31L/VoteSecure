import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSetupCommissioner, useRegisterVoter, useInitKeys, useResetAll, useCryptoParams } from '../api'
import { useElectionStore } from '../store'
import Alert from '../components/Alert'

export default function CreateElection() {
  const navigate = useNavigate()
  const setupComm = useSetupCommissioner()
  const registerVoter = useRegisterVoter()
  const initKeys = useInitKeys()
  const resetAll = useResetAll()
  const { cards, setSession } = useElectionStore()

  // If election already exists, go to dashboard
  useEffect(() => {
    if (cards.length > 0) navigate('/dashboard', { replace: true })
  }, [cards.length, navigate])

  const [title, setTitle] = useState('')
  const [options, setOptions] = useState('')
  const [voters, setVoters] = useState('')
  const [error, setError] = useState(null)
  const [step, setStep] = useState('') // current step label
  const [busy, setBusy] = useState(false)

  const handleCreate = async () => {
    const opts = options.split('\n').map((s) => s.trim()).filter(Boolean)
    const voterList = voters.split('\n').map((line) => {
      const parts = line.split(',').map((s) => s.trim())
      const name = parts[0] || ''
      const email = parts[1] || ''
      return { name, email }
    }).filter((v) => v.name)

    if (!title.trim()) { setError('Titre requis'); return }
    if (opts.length < 2) { setError('Au moins 2 options requises'); return }
    if (voterList.length < 1) { setError('Au moins un électeur requis'); return }
    const missingEmails = voterList.filter((v) => !v.email)
    if (missingEmails.length > 0) { setError(`Email manquant pour : ${missingEmails.map((v) => v.name).join(', ')}`); return }

    setError(null)
    setBusy(true)

    try {
      // Step 0: Reset all services first (clear stale data)
      setStep('Réinitialisation…')
      try { await resetAll.mutateAsync() } catch {}

      // Step 1: Setup commissioner
      setStep('Configuration du commissaire…')
      const r1 = await setupComm.mutateAsync({ title: title.trim(), candidates: opts })
      if (r1.error) throw new Error(`Commissaire : ${r1.error}`)

      // Step 2: Generate keys
      setStep('Génération des clés RSA…')
      const [d2, d3] = await Promise.all([
        initKeys.mutateAsync(),
      ])
      // initKeys already does both admin + counter

      // Step 3: Register voters
      setStep('Inscription des électeurs…')
      const cards = []
      for (const { name, email } of voterList) {
        const cd = await registerVoter.mutateAsync({ name, email })
        if (cd.ok) {
          cards.push({
            name,
            email,
            N1_fmt: cd.N1_formatted,
            N2_fmt: cd.N2_formatted,
            tth_N2: cd.tth_N2,
            email_sent: cd.email_sent,
          })
        }
      }

      // Save to store and navigate
      setSession(cards, voterList.length, title.trim())
      navigate('/dashboard')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
      setStep('')
    }
  }

  return (
    <div className="max-w-xl mx-auto px-6 py-12">
      <div className="mb-8">
        <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-[0.2em] mb-2 font-mono">Organisateur</p>
        <h2 className="font-display text-2xl font-black text-white tracking-tight">Créer un scrutin</h2>
        <p className="text-slate-400 mt-2">Configure le commissaire, génère les clés RSA et inscrit les électeurs.</p>
      </div>

      <div className="bg-surface-2 border border-surface-5 rounded-2xl p-6">
        <div className="mb-5">
          <label className="block text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-1.5 font-mono">Titre / Question du vote</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="ex : Meilleur projet de l'année"
            maxLength={80}
            className="w-full bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all"
          />
        </div>

        <div className="mb-5">
          <label className="block text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-1.5 font-mono">
            Candidats / Options{' '}
            <span className="normal-case tracking-normal font-normal text-slate-500">(un par ligne, min. 2)</span>
          </label>
          <textarea
            value={options}
            onChange={(e) => setOptions(e.target.value)}
            placeholder={"Candidat A\nCandidat B\nCandidat C"}
            rows={4}
            className="w-full bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all resize-y min-h-[100px] leading-relaxed"
          />
        </div>

        <hr className="border-surface-5 my-5" />

        <div className="mb-5">
          <label className="block text-[0.7rem] font-bold text-brand-400 uppercase tracking-widest mb-1.5 font-mono">
            Électeurs{' '}
            <span className="normal-case tracking-normal font-normal text-slate-500">(nom, email — un par ligne)</span>
          </label>
          <textarea
            value={voters}
            onChange={(e) => setVoters(e.target.value)}
            placeholder={"Ariane Dupont, ariane@mail.com\nMohammed Aït, mohammed@mail.com\nYasmine Benali, yasmine@mail.com"}
            rows={4}
            className="w-full bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 outline-none transition-all resize-y min-h-[100px] leading-relaxed"
          />
        </div>

        {error && <Alert type="error" className="mb-4">{error}</Alert>}

        <button
          onClick={handleCreate}
          disabled={busy}
          className="w-full inline-flex items-center justify-center gap-2 bg-brand-600 text-white font-display font-extrabold px-6 py-4 rounded-2xl text-base hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-lg shadow-brand-600/20"
        >
          {busy && <Spinner />}
          {step || 'Lancer le scrutin →'}
        </button>
      </div>
    </div>
  )
}

function Spinner() {
  return <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
}
