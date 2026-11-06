import { Link } from 'react-router'
import { Icon, type IconName } from './Icon'

export interface NavItemProps {
  icon?: IconName
  label: string
  active?: boolean
  count?: number
  href?: string
  /** Abre en pestaña nueva (Grafana, Jira) */
  external?: boolean
  onClick?: () => void
}

export function NavItem({ icon, label, active, count, href, external, onClick }: NavItemProps) {
  const content = (
    <>
      {icon && <Icon name={icon} size={16} />}
      <span className="nt-nav-label">{label}</span>
      {count !== undefined && <span className="nt-nav-count">{count}</span>}
      {external && (
        <>
          <Icon name="external" size={14} className="nt-nav-ext" />
          <span className="nt-sr-only">(se abre en una pestaña nueva)</span>
        </>
      )}
    </>
  )
  const current = active ? 'page' : undefined

  if (href && external) {
    return <a className="nt-nav" href={href} target="_blank" rel="noopener noreferrer" onClick={onClick}>{content}</a>
  }
  if (href) {
    return <Link className="nt-nav" to={href} aria-current={current} onClick={onClick}>{content}</Link>
  }
  return <button type="button" className="nt-nav" aria-current={current} onClick={onClick}>{content}</button>
}
