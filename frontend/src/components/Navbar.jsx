import { Link, useLocation } from 'react-router-dom'
import { useServices } from '../api'
import { useElectionStore } from '../store'

export default function Navbar() {
  const location = useLocation()
  const { data: services } = useServices()
  const hasElection = useElectionStore((s) => s.cards.length > 0)

  const onlineCount = services
    ? Object.values(services).filter((s) => s.status === 'ok').length
    : 0
  const totalServices = services ? Object.keys(services).length : 4

  return (
    <nav className="sticky top-0 z-50 bg-surface-0/80 backdrop-blur-xl border-b border-surface-4">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-brand-400 flex items-center justify-center shadow-lg shadow-brand-600/25 group-hover:shadow-brand-500/40 transition-shadow">
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          </div>
          <span className="font-display font-extrabold text-lg text-white tracking-tight">
            Vote<span className="text-brand-400">Secure</span>
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-500 mr-3">
            <span className={`w-2 h-2 rounded-full ${onlineCount === totalServices ? 'bg-neon-green animate-pulse' : onlineCount > 0 ? 'bg-neon-orange' : 'bg-slate-600'}`} />
            {onlineCount}/{totalServices}
          </div>

          {[
            { to: '/', label: 'Accueil' },
            { to: '/services', label: 'Services' },
            { to: hasElection ? '/dashboard' : '/create', label: hasElection ? 'Scrutin' : 'Créer' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
                location.pathname === to
                  ? 'bg-brand-600/15 text-brand-300'
                  : 'text-slate-400 hover:bg-surface-3 hover:text-white'
              }`}
            >
              {label}
            </Link>
          ))}
          <a
            href="/vote"
            target="_blank"
            rel="noopener"
            className="px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:bg-surface-3 hover:text-white transition-colors"
          >
            Voter
          </a>
        </div>
      </div>
    </nav>
  )
}
