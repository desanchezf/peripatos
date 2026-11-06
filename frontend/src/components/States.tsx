import type { ReactNode } from 'react'
import { useAuth } from '../auth/AuthContext'
import { Icon, type IconName } from './Icon'

export function Loading() {
  return <p className="pt-loading nt-muted" role="status">Cargando…</p>
}

/** Sin contenido todavía. A quien administra le indica dónde crearlo */
export function EmptyState({ icon, title, adminPath, children }: { icon: IconName; title: string; adminPath?: string; children?: ReactNode }) {
  const { user } = useAuth()
  return (
    <div className="nt-empty">
      <Icon name={icon} size={32} />
      <h2 className="t-title-3">{title}</h2>
      {children && <p className="nt-muted">{children}</p>}
      {user?.is_staff && adminPath && <a href={adminPath}>Añadir desde el admin</a>}
    </div>
  )
}
