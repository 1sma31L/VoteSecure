import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSetupCommissioner, useRegisterVoter, useInitKeys, useResetAll, useCryptoParams, useBulkRegisterVoters } from '../api'
import { useElectionStore } from '../store'
import Alert from '../components/Alert'

function Btn({ slug, alt, onClick, disabled, className = '' }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`clay-img-btn ${className}`}
    >
      <img src={`/assets/buttons/btn-${slug}.png`} alt={alt} className="block h-auto pointer-events-none select-none" draggable={false} />
    </button>
  )
}

export default function CreateElection() {
  const navigate = useNavigate()
  const setupComm = useSetupCommissioner()
  const registerVoter = useRegisterVoter()
  const bulkRegisterVoters = useBulkRegisterVoters()
  const initKeys = useInitKeys()
  const resetAll = useResetAll()
  const { cards, setSession } = useElectionStore()

  useEffect(() => {
    if (cards.length > 0) navigate('/dashboard', { replace: true })
  }, [cards.length, navigate])

  const [title, setTitle]   = useState('')
  const [options, setOptions] = useState('')
  const [voters, setVoters]   = useState('')
  const [error, setError]     = useState(null)
  const [step, setStep]       = useState('')
  const [busy, setBusy]       = useState(false)
  const fileInputRef          = useRef(null)

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    try {
      const fileName = file.name.toLowerCase()
      if (!fileName.endsWith('.csv') && !fileName.endsWith('.txt')) {
        setError('Veuillez sélectionner un fichier CSV ou TXT')
        return
      }
      const content = await file.text()
      const lines = content.trim().split('\n')
      const parsed = []
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim()
        if (!line) continue
        const cols = line.split(',').map(c => c.trim().replace(/^"|"$/g, ''))
        if (i === 0 && (cols[0]?.toLowerCase().includes('timestamp') || cols[0]?.toLowerCase().includes('horodateur') || cols[1]?.toLowerCase().includes('email'))) continue
        if (cols.length >= 3) {
          const email = cols[1], name = cols[2]
          if (email && name && email.includes('@')) parsed.push(`${name}, ${email}`)
        }
      }
      if (parsed.length === 0) { setError('Aucun électeur valide trouvé dans le fichier'); return }
      setVoters(parsed.join('\n'))
    } catch (err) {
      setError(`Erreur lecture fichier: ${err.message}`)
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleCreate = async () => {
    const opts = options.split('\n').map(s => s.trim()).filter(Boolean)
    const voterList = voters.split('\n').map(line => {
      const parts = line.split(',').map(s => s.trim())
      return { name: parts[0] || '', email: parts[1] || '' }
    }).filter(v => v.name)

    if (!title.trim())           { setError('Titre requis'); return }
    if (opts.length < 2)         { setError('Au moins 2 options requises'); return }
    if (voterList.length < 1)    { setError('Au moins un électeur requis'); return }
    const missingEmails = voterList.filter(v => !v.email)
    if (missingEmails.length > 0) { setError(`Email manquant pour : ${missingEmails.map(v => v.name).join(', ')}`); return }

    setError(null)
    setBusy(true)
    try {
      setStep('Réinitialisation…')
      try { await resetAll.mutateAsync() } catch {}

      setStep('Configuration du commissaire…')
      const r1 = await setupComm.mutateAsync({ title: title.trim(), candidates: opts })
      if (r1.error) throw new Error(`Commissaire : ${r1.error}`)

      setStep('Génération des clés RSA…')
      await initKeys.mutateAsync()

      setStep('Inscription des électeurs…')
      const cards = []
      if (voterList.length > 1) {
        const blob = new Blob([voters], { type: 'text/plain' })
        const file = new File([blob], 'voters.txt', { type: 'text/plain' })
        const result = await bulkRegisterVoters.mutateAsync(file)
        if (result.ok) {
          for (const voter of result.voters) {
            cards.push({ name: voter.name, email: voter.email, N1_fmt: voter.N1_formatted, N2_fmt: voter.N2_formatted, tth_N2: voter.tth_N2, email_sent: voter.email_sent })
          }
        }
      } else {
        for (const { name, email } of voterList) {
          const cd = await registerVoter.mutateAsync({ name, email })
          if (cd.ok) cards.push({ name, email, N1_fmt: cd.N1_formatted, N2_fmt: cd.N2_formatted, tth_N2: cd.tth_N2, email_sent: cd.email_sent })
        }
      }

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
    <div className="clay-page-inner">
      <div className="clay-page-header">
        <p className="clay-label">Organisateur</p>
        <h2 className="clay-page-title">Créer un scrutin</h2>
        <p className="clay-page-sub">Configure le commissaire, génère les clés RSA et inscrit les électeurs.</p>
      </div>

      <div className="clay-card">
        {/* Title */}
        <div className="clay-field">
          <label className="clay-field-label">Titre / Question du vote</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="ex : Meilleur projet de l'année"
            maxLength={80}
            className="clay-input"
          />
        </div>

        {/* Options */}
        <div className="clay-field">
          <label className="clay-field-label">
            Candidats / Options <span className="clay-field-hint">(un par ligne, min. 2)</span>
          </label>
          <textarea
            value={options}
            onChange={e => setOptions(e.target.value)}
            placeholder={"Candidat A\nCandidat B\nCandidat C"}
            rows={4}
            className="clay-textarea"
          />
        </div>

        <hr className="clay-divider" />

        {/* Voters */}
        <div className="clay-field">
          <label className="clay-field-label">
            Électeurs <span className="clay-field-hint">(nom, email — un par ligne)</span>
          </label>
          <div className="clay-btn-row mb-3">
            <Btn slug="import" alt="Importer CSV/TXT" onClick={() => fileInputRef.current?.click()} disabled={busy} />
            <input ref={fileInputRef} type="file" accept=".csv,.txt" onChange={handleFileUpload} className="hidden" />
            {voters.trim() && (
              <Btn slug="effacer" alt="Effacer" onClick={() => setVoters('')} disabled={busy} />
            )}
          </div>
          <textarea
            value={voters}
            onChange={e => setVoters(e.target.value)}
            placeholder={"Ariane Dupont, ariane@mail.com\nMohammed Aït, mohammed@mail.com"}
            rows={4}
            className="clay-textarea"
          />
          <p className="clay-field-note">
            Format : <code className="clay-code">Nom, email@example.com</code> (un par ligne)
          </p>
        </div>

        {error && <Alert type="error" className="mb-4">{error}</Alert>}

        {/* Submit button */}
        <div className="flex justify-center mt-2">
          {busy ? (
            <div className="clay-busy-state">
              <span className="clay-spinner" />
              <span className="clay-busy-label">{step || 'Traitement…'}</span>
            </div>
          ) : (
            <Btn slug="lancer" alt="Lancer le scrutin" onClick={handleCreate} disabled={busy} className="clay-btn-lg" />
          )}
        </div>
      </div>
    </div>
  )
}
