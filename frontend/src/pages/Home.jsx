import { Link, useNavigate } from 'react-router-dom'
import { useServices } from '../api'
import { useElectionStore } from '../store'

// ─── BUTTON ASSET HELPER ──────────────────────────────────────────────────────
// All buttons are image assets placed in /public/assets/buttons/
// Naming convention: btn-{slug}.png
// Available assets (you provide these as PNG images):
//   btn-organiser.png    → "Organiser un scrutin →"
//   btn-voter.png        → "Voter →"
//   btn-services.png     → "Services"
//   btn-creer.png        → "Créer"
//   btn-accueil.png      → "Accueil"
//   btn-ouvrir.png       → "▶ Ouvrir le vote"
//   btn-cloture.png      → "⏹ Clôturer & dépouiller"
//   btn-init-keys.png    → "⚙ Initialiser les clés RSA"
//   btn-reset.png        → "↺ Réinitialiser tout"
//   btn-lancer.png       → "Lancer le scrutin →"
//   btn-verifier.png     → "Vérifier mon identité →"
//   btn-signer.png       → "Signer & soumettre mon bulletin"
//   btn-resultats.png    → "↻ Vérifier les résultats"
//   btn-import.png       → "📁 Importer CSV/TXT"
//   btn-effacer.png      → "✕ Effacer"
//   btn-retour.png       → "← Retour à l'accueil"
//   btn-commencer.png    → "🗳 Commencer maintenant →"

function Btn({ slug, alt, onClick, disabled, className = '', style = {}, type = 'button' }) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`relative inline-block border-0 bg-transparent p-0 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed transition-transform hover:scale-[1.03] active:scale-[0.97] focus:outline-none ${className}`}
      style={style}
    >
      <img
        src={`/assets/buttons/btn-${slug}.png`}
        alt={alt}
        className="block h-auto pointer-events-none select-none"
        draggable={false}
      />
    </button>
  )
}

// ─── DATA ─────────────────────────────────────────────────────────────────────

const SERVICES_LIST = [
  { key: 'commissioner', label: 'Commissaire', port: ':5001', icon: '👤', colorKey: 'blue',
    desc: 'Inscrit les électeurs, génère N1/N2, valide l\'identité' },
  { key: 'administrator', label: 'Administrateur', port: ':5002', icon: '🔐', colorKey: 'green',
    desc: 'Génère les clés RSA, signe les bulletins à l\'aveugle' },
  { key: 'anonymiser', label: 'Anonymiseur', port: ':5003', icon: '🎭', colorKey: 'amber',
    desc: 'Casse le lien N1 ↔ bulletin chiffré' },
  { key: 'counter', label: 'Décompteur', port: ':5004', icon: '📊', colorKey: 'green',
    desc: 'Déchiffre, vérifie et comptabilise les votes' },
  { key: 'web', label: 'Site Web', port: ':5000', icon: '🖥', colorKey: 'blue',
    desc: 'Interface électeur, crypto 100 % côté navigateur' },
]

const LIFECYCLE = [
  { n: 1, title: 'Initialisation', icon: '⚙',
    desc: 'Administrateur et décompteur génèrent leurs paires de clés RSA-2048. Les clés publiques sont partagées pour le chiffrement côté client.' },
  { n: 2, title: 'Configuration', icon: '📋',
    desc: 'Le commissaire reçoit le titre du scrutin et la liste des candidats, et entre en phase d\'inscription.' },
  { n: 3, title: 'Inscription', icon: '👤',
    desc: 'Le commissaire génère N1 (identification) et N2 (authentification) pour chaque électeur. tth(N2) est stocké pour vérification.' },
  { n: 4, title: 'Ouverture du vote', icon: '🔓',
    desc: 'Le commissaire ouvre le scrutin. Les électeurs peuvent soumettre leurs bulletins signés à l\'aveugle.' },
  { n: 5, title: 'Vote côté navigateur', icon: '🗳',
    desc: 'L\'électeur entre N1 et N2. Le navigateur calcule h(choice|N2), aveugle le message et l\'envoie pour signature.' },
  { n: 6, title: 'Signature aveugle', icon: '🔏',
    desc: 'L\'administrateur signe le message aveuglé sans voir le contenu. L\'électeur désaveugle et vérifie localement.' },
  { n: 7, title: 'Soumission du bulletin', icon: '📨',
    desc: 'Bulletin chiffré + signature RSA + N1. L\'anonymiseur casse le lien N1↔bulletin avant transmission.' },
  { n: 8, title: 'Dépouillement', icon: '📊',
    desc: 'Le décompteur déchiffre, vérifie les signatures et tth(N2), puis publie les résultats.' },
]

const FEATURES = [
  { icon: '🔐', title: 'RSA 2048-bit', desc: 'Chaque entité possède sa propre paire de clés. Seul le décompteur peut déchiffrer les bulletins.' },
  { icon: '🔏', title: 'Signature aveugle', desc: 'L\'administrateur signe sans voir le vote. L\'identité et le contenu ne sont jamais associés.' },
  { icon: '🎭', title: 'Anonymat fort', desc: 'L\'anonymiseur sépare identité et contenu chiffré. Aucune entité ne peut corréler les deux.' },
  { icon: '✅', title: 'Vérifiabilité', desc: 'Signature RSA vérifiable côté client, tth(N2) garantit l\'authenticité, trace crypto disponible.' },
  { icon: '🖥', title: 'Crypto côté client', desc: 'Hachage, aveuglement, désaveuglement et vérification s\'exécutent dans le navigateur — rien ne transite en clair.' },
  { icon: '🌐', title: 'Architecture distribuée', desc: '5 services indépendants. La compromission d\'une seule entité ne suffit pas à casser le système.' },
]

// ─── DOT INDICATOR ────────────────────────────────────────────────────────────
const dotColor = {
  blue:  'bg-[#1E3A6E]',
  green: 'bg-[#3D7A4E]',
  amber: 'bg-[#B8860B]',
}

export default function Home() {
  const { data: services } = useServices()
  const hasElection = useElectionStore((s) => s.cards.length > 0)
  const navigate = useNavigate()

  const getStatus = (key) => {
    if (!services) return false
    const svc = services[key] || services[key === 'web' ? 'web' : key]
    return svc?.status === 'ok'
  }

  return (
    <div className="clay-page">

      {/* ═══ HERO ═══════════════════════════════════════════════════════════ */}
      <section className="clay-hero">
        {/* pill badge */}
        <div className="clay-pill mb-10">
          <span className="clay-dot clay-dot--green" />
          <span className="clay-pill-text">RSA-2048 · Signatures aveugles · TTH · 5 entités</span>
        </div>

        {/* headline */}
        <img
  src="/assets/buttons/mainlogo.png"
  alt="VoteSecure"
  className="clay-hero-logo"
/>
        <p className="clay-hero-sub">Scrutin électronique cryptographique distribué</p>
        <p className="clay-hero-body">
          Un système de vote où <strong className="clay-strong">aucune entité seule</strong> ne peut ni identifier un électeur ni connaître son vote.
          5 services indépendants, du chiffrement RSA à la signature aveugle de Chaum.
        </p>

        {/* CTA BUTTONS — image assets */}
        <div className="clay-cta-row">
          <Btn
            slug="organiser"
            alt="Organiser un scrutin"
            onClick={() => navigate(hasElection ? '/dashboard' : '/create')}
            className="clay-btn-lg"
          />
          <Btn
            slug="voter"
            alt="Voter"
            onClick={() => window.open('/vote', '_blank')}
            className="clay-btn-lg"
          />
        </div>
      </section>

      {/* ═══ SERVICE STATUS ══════════════════════════════════════════════════ */}
      <section className="clay-section clay-section--narrow">
        <div className="clay-services-grid">
          {SERVICES_LIST.map((svc) => {
            const online = getStatus(svc.key)
            return (
              <div key={svc.key} className="clay-service-card">
                <span className="clay-service-icon">{svc.icon}</span>
                <span className="clay-service-label">{svc.label}</span>
                <div className="clay-service-port-row">
                  <span className={`clay-dot ${online ? dotColor[svc.colorKey] : 'bg-[#BFB9AF]'}`} />
                  <span className="clay-service-port">{svc.port}</span>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ═══ PROTOCOL LIFECYCLE ══════════════════════════════════════════════ */}
      <section className="clay-section">
        <div className="clay-section-header">
          <p className="clay-label">Protocole</p>
          <h2 className="clay-section-title">Comment ça fonctionne</h2>
          <p className="clay-section-sub">8 étapes, de l'initialisation au dépouillement.</p>
        </div>
        <div className="clay-lifecycle-list">
          {LIFECYCLE.map((step) => (
            <div key={step.n} className="clay-lifecycle-row">
              <div className="clay-lifecycle-num">{step.n}</div>
              <div className="clay-lifecycle-card">
                <div className="clay-lifecycle-head">
                  <span className="clay-lifecycle-icon">{step.icon}</span>
                  <h3 className="clay-lifecycle-title">{step.title}</h3>
                </div>
                <p className="clay-lifecycle-desc">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ FEATURES ════════════════════════════════════════════════════════ */}
      <section className="clay-section clay-section--tinted">
        <div className="clay-section-header">
          <p className="clay-label">Garanties cryptographiques</p>
          <h2 className="clay-section-title">Pourquoi c'est sécurisé</h2>
          <p className="clay-section-sub">Chaque propriété est garantie par la cryptographie, pas par la confiance.</p>
        </div>
        <div className="clay-features-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className="clay-feature-card">
              <div className="clay-feature-icon">{f.icon}</div>
              <h3 className="clay-feature-title">{f.title}</h3>
              <p className="clay-feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CTA BOTTOM ══════════════════════════════════════════════════════ */}
      <section className="clay-section clay-section--center">
        <h2 className="clay-section-title" style={{ marginBottom: '0.5rem' }}>Prêt à organiser un scrutin ?</h2>
        <p className="clay-section-sub" style={{ marginBottom: '2.5rem' }}>Lancez un vote en quelques clics. L'inscription, la signature aveugle et le dépouillement sont automatisés.</p>
        <Btn
          slug="commencer"
          alt="Commencer maintenant"
          onClick={() => navigate(hasElection ? '/dashboard' : '/create')}
          className="clay-btn-lg"
        />
      </section>

    </div>
  )
}

// Export Btn so other components can import it from here or from a shared location
export { Btn }
