import { Link } from 'react-router-dom'
import { useServices } from '../api'
import { useElectionStore } from '../store'

const SERVICES = [
  { key: 'commissioner', label: 'Commissaire', port: ':5001', color: 'neon-blue', desc: 'Inscrit les électeurs, génère les codes N1/N2, valide l\'identité, vérifie tth(N2)' },
  { key: 'administrator', label: 'Administrateur', port: ':5002', color: 'neon-cyan', desc: 'Génère les clés RSA, signe les bulletins à l\'aveugle sans voir le contenu' },
  { key: 'anonymiser', label: 'Anonymiseur', port: ':5003', color: 'neon-orange', desc: 'Casse le lien entre N1 (identité) et le bulletin chiffré' },
  { key: 'counter', label: 'Décompteur', port: ':5004', color: 'neon-green', desc: 'Déchiffre les bulletins, vérifie les signatures, comptabilise les votes' },
]

const LIFECYCLE = [
  { n: 1, title: 'Initialisation', icon: '⚙', color: 'neon-blue',
    desc: 'L\'administrateur et le décompteur génèrent leurs paires de clés RSA (2048 bits). Les clés publiques sont partagées avec le site web pour le chiffrement côté client.' },
  { n: 2, title: 'Configuration', icon: '📋', color: 'neon-cyan',
    desc: 'Le commissaire reçoit le titre du scrutin et la liste des candidats. Il prépare la session et entre en phase d\'inscription des électeurs.' },
  { n: 3, title: 'Inscription', icon: '👤', color: 'neon-orange',
    desc: 'Chaque électeur est inscrit par le commissaire qui génère un code N1 (identification) et un code N2 (authentification). Le hash tth(N2) est stocké pour vérification ultérieure.' },
  { n: 4, title: 'Ouverture du vote', icon: '🔓', color: 'neon-green',
    desc: 'Le commissaire ouvre le scrutin. Les électeurs peuvent maintenant soumettre leurs bulletins signés à l\'aveugle.' },
  { n: 5, title: 'Vote — Côté navigateur', icon: '🗳', color: 'neon-pink',
    desc: 'L\'électeur entre N1 et N2. Le navigateur calcule h(choice|N2), aveugle le message avec un facteur aléatoire k, et envoie le message aveuglé à l\'administrateur pour signature.' },
  { n: 6, title: 'Signature aveugle', icon: '🔏', color: 'neon-cyan',
    desc: 'L\'administrateur signe le message aveuglé avec sa clé privée RSA sans jamais voir le contenu. L\'électeur désaveugle la signature localement et vérifie son authenticité.' },
  { n: 7, title: 'Soumission du bulletin', icon: '📨', color: 'neon-orange',
    desc: 'Le bulletin contient le vote chiffré avec la clé du décompteur, la signature de l\'administrateur, et N1. L\'anonymiseur casse le lien N1↔bulletin avant transmission au décompteur.' },
  { n: 8, title: 'Dépouillement', icon: '📊', color: 'neon-green',
    desc: 'Le décompteur déchiffre chaque bulletin avec sa clé privée, vérifie la signature de l\'administrateur et tth(N2), puis comptabilise les votes et publie les résultats.' },
]

const FEATURES = [
  { icon: '🔐', title: 'RSA 2048-bit', desc: 'Chaque entité possède sa propre paire de clés. Le vote est chiffré avec la clé publique du décompteur — seul lui peut déchiffrer.' },
  { icon: '🔏', title: 'Signature aveugle', desc: 'L\'administrateur signe sans voir le vote. L\'électeur prouve son droit de vote via N1, mais l\'administrateur ne connaît jamais le contenu du bulletin.' },
  { icon: '🎭', title: 'Anonymat fort', desc: 'L\'anonymiseur sépare l\'identité (N1) du contenu chiffré. Aucune entité ne peut à la fois identifier l\'électeur ET connaître son vote.' },
  { icon: '✅', title: 'Vérifiabilité', desc: 'Chaque étape est vérifiable : la signature RSA est contrôlée côté client, tth(N2) garantit l\'authenticité, et la trace crypto est disponible après vote.' },
  { icon: '🖥', title: 'Crypto côté client', desc: 'Toutes les opérations cryptographiques de l\'électeur (hachage, aveuglement, désaveuglement, vérification) s\'exécutent dans le navigateur — rien ne transite en clair.' },
  { icon: '🌐', title: 'Architecture distribuée', desc: '5 services indépendants sur 5 machines. La compromission d\'une seule entité ne suffit pas pour casser l\'anonymat ou falsifier un vote.' },
]

const TEAM = [
  { name: 'Membre A', role: 'Backend — API & Services', color: 'neon-blue', icon: '⚙',
    desc: 'Développement du backend Flask, proxy API, et orchestration des 4 microservices (commissaire, administrateur, anonymiseur, décompteur).' },
  { name: 'Membre B', role: 'Frontend — Interface & UX', color: 'neon-cyan', icon: '🎨',
    desc: 'Conception de l\'interface React, intégration React Query, expérience électeur, et design du tableau de bord organisateur.' },
  { name: 'Membre C', role: 'RSA & Chiffrement', color: 'neon-green', icon: '🔐',
    desc: 'Implémentation des primitives RSA (génération de clés, chiffrement, déchiffrement), modular exponentiation, et gestion des grands entiers.' },
  { name: 'Membre D', role: 'Entités distribuées', color: 'neon-orange', icon: '🌐',
    desc: 'Architecture des 4 entités indépendantes, protocoles de communication, anonymiseur, et séparation des responsabilités.' },
  { name: 'Membre E', role: 'Signature aveugle & Vérification', color: 'neon-pink', icon: '🔏',
    desc: 'Protocole de signature aveugle Chaum, vérification côté client, preuve de validité des bulletins, et intégration tth(N2).' },
]

const colorMap = {
  'neon-blue': { bg: 'bg-neon-blue/10', border: 'border-neon-blue/20', text: 'text-neon-blue', dot: 'bg-neon-blue', glow: 'shadow-neon-blue/20' },
  'neon-cyan': { bg: 'bg-neon-cyan/10', border: 'border-neon-cyan/20', text: 'text-neon-cyan', dot: 'bg-neon-cyan', glow: 'shadow-neon-cyan/20' },
  'neon-green': { bg: 'bg-neon-green/10', border: 'border-neon-green/20', text: 'text-neon-green', dot: 'bg-neon-green', glow: 'shadow-neon-green/20' },
  'neon-orange': { bg: 'bg-neon-orange/10', border: 'border-neon-orange/20', text: 'text-neon-orange', dot: 'bg-neon-orange', glow: 'shadow-neon-orange/20' },
  'neon-pink': { bg: 'bg-neon-pink/10', border: 'border-neon-pink/20', text: 'text-neon-pink', dot: 'bg-neon-pink', glow: 'shadow-neon-pink/20' },
}

export default function Home() {
  const { data: services } = useServices()
  const hasElection = useElectionStore((s) => s.cards.length > 0)

  return (
    <div className="relative">
      {/* ═══════════════════════════════════════════════════════════════════
          HERO
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-glow-blue" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-brand-700/10 blur-3xl" />
        <div className="relative max-w-5xl mx-auto px-6 pt-28 pb-32 text-center">
          <div className="inline-flex items-center gap-2.5 bg-surface-3 border border-surface-5 rounded-full px-5 py-2 mb-8">
            <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <span className="text-xs font-mono font-semibold text-slate-400 tracking-wide">RSA-2048 · Signatures aveugles · TTH · 5 entités</span>
          </div>
          <h1 className="font-display text-5xl sm:text-7xl lg:text-8xl font-black text-white tracking-tight leading-[0.95] mb-6">
            VoteSecure
          </h1>
          <p className="font-display text-xl sm:text-2xl font-light text-brand-300 tracking-wide mb-4">
            Scrutin électronique cryptographique distribué
          </p>
          <p className="text-base text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed">
            Un système de vote où <span className="text-neon-cyan font-semibold">aucune entité seule</span> ne peut ni identifier un électeur ni connaître son vote.
            5 services indépendants, du chiffrement RSA à la signature aveugle de Chaum.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to={hasElection ? '/dashboard' : '/create'}
              className="group inline-flex items-center gap-3 bg-brand-600 text-white font-display font-bold px-8 py-4 rounded-2xl shadow-lg shadow-brand-600/25 hover:bg-brand-500 hover:shadow-brand-500/30 hover:-translate-y-0.5 transition-all text-base"
            >
              <span className="text-lg">🗳</span>
              {hasElection ? 'Tableau de bord' : 'Organiser un scrutin'}
              <span className="text-white/50 group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>
            <a
              href="/vote"
              target="_blank"
              rel="noopener"
              className="inline-flex items-center gap-3 bg-surface-3 border border-surface-5 text-slate-300 font-display font-semibold px-8 py-4 rounded-2xl hover:bg-surface-4 hover:border-brand-700/40 hover:text-white transition-all text-base"
            >
              Voter →
            </a>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          SERVICES STATUS
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-5xl mx-auto px-6 -mt-10 mb-20 relative z-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {SERVICES.map((svc) => {
            const online = services?.[svc.key]?.status === 'ok'
            const c = colorMap[svc.color]
            return (
              <div key={svc.key} className={`bg-surface-2 border ${c.border} rounded-xl px-4 py-3.5 flex items-center gap-3`}>
                <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${online ? `${c.dot} animate-pulse` : 'bg-slate-600'}`} />
                <div className="min-w-0">
                  <div className={`text-sm font-bold ${online ? c.text : 'text-slate-500'} truncate`}>{svc.label}</div>
                  <div className="text-[0.6rem] text-slate-500 font-mono">{svc.port}</div>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          VOTE LIFECYCLE
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-5xl mx-auto px-6 pb-24">
        <div className="text-center mb-14">
          <p className="text-[0.7rem] font-bold text-brand-400 uppercase tracking-[0.2em] mb-3 font-mono">Parcours complet</p>
          <h2 className="font-display text-3xl sm:text-4xl font-black text-white tracking-tight">Cycle de vie du vote</h2>
          <p className="text-slate-400 mt-3 max-w-lg mx-auto">De l'initialisation des clés à la publication des résultats, chaque étape est cryptographiquement sécurisée.</p>
        </div>
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-surface-5 hidden sm:block" />
          <div className="space-y-6">
            {LIFECYCLE.map((step) => {
              const c = colorMap[step.color]
              return (
                <div key={step.n} className="relative flex gap-5 sm:gap-8">
                  <div className={`shrink-0 w-12 h-12 rounded-xl ${c.bg} border ${c.border} flex items-center justify-center text-xl z-10`}>
                    {step.icon}
                  </div>
                  <div className={`flex-1 bg-surface-2 border ${c.border} rounded-2xl p-5 sm:p-6`}>
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`font-mono text-xs font-bold ${c.text}`}>Étape {step.n}</span>
                      <h3 className="font-display text-lg font-bold text-white">{step.title}</h3>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          FEATURES
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-glow-cyan" />
        <div className="relative max-w-5xl mx-auto px-6 py-24">
          <div className="text-center mb-14">
            <p className="text-[0.7rem] font-bold text-neon-cyan uppercase tracking-[0.2em] mb-3 font-mono">Garanties cryptographiques</p>
            <h2 className="font-display text-3xl sm:text-4xl font-black text-white tracking-tight">Pourquoi c'est sécurisé</h2>
            <p className="text-slate-400 mt-3 max-w-lg mx-auto">Chaque propriété de sécurité est garantie par la cryptographie, pas par la confiance.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <div key={i} className="bg-surface-2 border border-surface-5 rounded-2xl p-6 hover:border-brand-700/40 transition-colors group">
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="font-display text-lg font-bold text-white mb-2 group-hover:text-brand-300 transition-colors">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          ARCHITECTURE DIAGRAM
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-5xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <p className="text-[0.7rem] font-bold text-neon-orange uppercase tracking-[0.2em] mb-3 font-mono">Infrastructure</p>
          <h2 className="font-display text-3xl sm:text-4xl font-black text-white tracking-tight">Architecture distribuée</h2>
          <p className="text-slate-400 mt-3 max-w-lg mx-auto">Chaque entité ne voit que ce qu'elle doit voir. La compromission d'une seule ne compromet pas le système.</p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {[...SERVICES, { key: 'web', label: 'Site Web', port: ':5000', color: 'neon-pink', desc: 'Interface électeur. Toute la crypto s\'exécute côté navigateur.' }].map((svc) => {
            const c = colorMap[svc.color]
            return (
              <div key={svc.key} className={`relative bg-surface-2 border ${c.border} rounded-2xl p-5 overflow-hidden group hover:border-opacity-50 transition-colors`}>
                <div className={`absolute top-0 left-0 right-0 h-0.5 ${c.dot} opacity-60`} />
                <div className={`w-10 h-10 ${c.bg} rounded-xl flex items-center justify-center font-mono text-xs font-bold ${c.text} mb-3`}>
                  {svc.port}
                </div>
                <h4 className="font-display text-sm font-bold text-white mb-1.5">{svc.label}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{svc.desc}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          TEAM
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-glow-blue" />
        <div className="relative max-w-5xl mx-auto px-6 py-24">
          <div className="text-center mb-14">
            <p className="text-[0.7rem] font-bold text-neon-pink uppercase tracking-[0.2em] mb-3 font-mono">Équipe projet</p>
            <h2 className="font-display text-3xl sm:text-4xl font-black text-white tracking-tight">Les constructeurs</h2>
            <p className="text-slate-400 mt-3 max-w-lg mx-auto">Cinq membres, cinq rôles — chacun responsable d'une brique critique du système.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {TEAM.map((m, i) => {
              const c = colorMap[m.color]
              return (
                <div key={i} className={`bg-surface-2 border ${c.border} rounded-2xl p-6 group hover:border-opacity-60 transition-colors`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-11 h-11 ${c.bg} rounded-xl flex items-center justify-center text-xl`}>
                      {m.icon}
                    </div>
                    <div>
                      <h3 className="font-display text-base font-bold text-white">{m.name}</h3>
                      <p className={`text-xs font-semibold ${c.text}`}>{m.role}</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed">{m.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          CTA
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-3xl mx-auto px-6 py-24 text-center">
        <h2 className="font-display text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Prêt à organiser un scrutin ?</h2>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">Lancez un vote en quelques clics. L'inscription, la signature aveugle et le dépouillement sont automatisés.</p>
        <Link
          to={hasElection ? '/dashboard' : '/create'}
          className="inline-flex items-center gap-3 bg-brand-600 text-white font-display font-bold px-10 py-5 rounded-2xl shadow-lg shadow-brand-600/25 hover:bg-brand-500 hover:shadow-brand-500/30 hover:-translate-y-0.5 transition-all text-lg"
        >
          🗳 Commencer maintenant →
        </Link>
      </section>
    </div>
  )
}
