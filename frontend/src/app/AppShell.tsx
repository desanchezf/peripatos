import { useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { IconButton, Loading, NavItem } from '../components'
import { Icon, type IconName } from '../components/Icon'
import { Logo } from './Logo'
import { useTheme } from './ThemeProvider'

const NAV: { icon: IconName; label: string; href: string }[] = [
  { icon: 'chart', label: 'Panel', href: '/' },
  { icon: 'book', label: 'Lecturas', href: '/readings' },
  { icon: 'task', label: 'Cuestionarios', href: '/quizzes' },
  { icon: 'flask', label: 'Laboratorios', href: '/labs' },
  { icon: 'route', label: 'Roadmap', href: '/roadmap' },
  { icon: 'graph', label: 'Trayectorias', href: '/paths' },
  { icon: 'chat', label: 'Asistente', href: '/assistant' },
]

/** Armazón: barra lateral (cajón en móvil) y la vista en el centro. Exige sesión. */
export default function AppShell() {
  const { user, loading, logout } = useAuth()
  const location = useLocation()
  const { mode, setMode } = useTheme()
  // El cajón se abre para la entrada del historial actual: al navegar se cierra
  const [drawerKey, setDrawerKey] = useState<string | null>(null)
  const drawerOpen = drawerKey === location.key

  if (loading) return <Loading />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />

  const isActive = (href: string) => (href === '/' ? location.pathname === '/' : location.pathname === href || location.pathname.startsWith(`${href}/`))

  return (
    <div className={['nt-ws', 'nt-app', 'nt-app-noassistant', drawerOpen && 'nt-app-drawer'].filter(Boolean).join(' ')}>
      <a className="nt-skip" href="#nt-main">Saltar al contenido</a>
      <nav className="nt-ws-side" aria-label="Navegación principal">
        <div className="nt-ws-brand"><Logo /><span>peripatos</span></div>
        {NAV.map((item) => <NavItem key={item.href} {...item} active={isActive(item.href)} />)}
        {user.is_staff && (
          <>
            <h2 className="nt-navgroup">Sistema</h2>
            <NavItem icon="shield" label="Administración" href="/admin/" external />
          </>
        )}
        <div className="nt-side-user">
          <Icon name="user" size={16} />
          <span className="nt-grow nt-ellipsis" title={user.username}>{user.username}</span>
          <IconButton
            icon={mode === 'dark' ? 'sun' : 'moon'}
            label={mode === 'dark' ? 'Usar tema claro' : 'Usar tema oscuro'}
            onClick={() => setMode(mode === 'dark' ? 'light' : 'dark')}
          />
          <IconButton icon="logout" label="Cerrar sesión" onClick={logout} />
        </div>
      </nav>
      {drawerOpen && <div className="nt-scrim" onClick={() => setDrawerKey(null)} aria-hidden />}
      <div className="nt-ws-main">
        <div className="nt-mobilebar">
          <IconButton icon="menu" label="Menú" aria-expanded={drawerOpen} onClick={() => setDrawerKey(drawerOpen ? null : location.key)} />
          <span className="nt-ws-brand nt-grow"><Logo />peripatos</span>
        </div>
        <main id="nt-main" className="nt-main" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
