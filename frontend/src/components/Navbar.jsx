import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useServices } from '../api'
import { useElectionStore } from '../store'

// ── Image button helper (same as in Home) ──────────────────────────────────
function NavBtn({ slug, alt, to, href, active, onClick }) {
  const base = `clay-nav-btn ${active ? 'clay-nav-btn--active' : ''}`

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener" className={base}>
        <img src={`/assets/buttons/btn-${slug}.png`} alt={alt} className="clay-nav-btn-img" draggable={false} />
      </a>
    )
  }

  if (to) {
    return (
      <Link to={to} className={base}>
        <img src={`/assets/buttons/btn-${slug}.png`} alt={alt} className="clay-nav-btn-img" draggable={false} />
      </Link>
    )
  }

  return (
    <button type="button" onClick={onClick} className={base}>
      <img src={`/assets/buttons/btn-${slug}.png`} alt={alt} className="clay-nav-btn-img" draggable={false} />
    </button>
  )
}

export default function Navbar() {
  const location = useLocation()
  const { data: services } = useServices()
  const hasElection = useElectionStore((s) => s.cards.length > 0)

  const onlineCount = services
    ? Object.values(services).filter((s) => s.status === 'ok').length
    : 0
  const totalServices = services ? Object.keys(services).length : 4

  const allOnline = onlineCount === totalServices
  const someOnline = onlineCount > 0

  const is = (path) => location.pathname === path

  return (
    <nav className="clay-navbar">
      <div className="clay-navbar-inner">
{/* Logo */}
<Link to="/" className="clay-logo">
  <img
    src="/assets/buttons/logo.png"
    alt="VoteSecure"
    className="clay-logo-img"
    draggable={false}
  />
</Link>



        {/* Nav items */}
        <div className="clay-nav-items">
          {/* Service status pill */}
          <div className="clay-status-pill hidden sm:flex">
            <span className={`clay-dot ${allOnline ? 'bg-[#3D7A4E] animate-pulse' : someOnline ? 'bg-[#B8860B]' : 'bg-[#BFB9AF]'}`} />
            <span className="clay-status-text">{onlineCount}/{totalServices}</span>
          </div>

          <NavBtn slug="accueil"   alt="Accueil"   to="/"         active={is('/')} />
          <NavBtn slug="services"  alt="Services"  to="/services" active={is('/services')} />
          <NavBtn
            slug={hasElection ? 'scrutin' : 'creer'}
            alt={hasElection ? 'Scrutin' : 'Créer'}
            to={hasElection ? '/dashboard' : '/create'}
            active={is('/dashboard') || is('/create')}
          />
          <NavBtn slug="voter" alt="Voter" href="/vote" />
        </div>

      </div>
    </nav>
  )
}
