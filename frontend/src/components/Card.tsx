import type * as React from 'react'
import { Icon, type IconName } from './Icon'

export interface CardProps {
  title?: string
  icon?: IconName
  /** Nodos a la derecha de la cabecera */
  actions?: React.ReactNode
  /** false para listas a sangre */
  padding?: boolean
  style?: React.CSSProperties
  children?: React.ReactNode
}

export function Card({ title, icon, actions, padding = true, style, children }: CardProps) {
  return (
    <section className="nt-card" style={style}>
      {(title || icon || actions) && (
        <header className="nt-card-head">
          {icon && <Icon name={icon} size={18} />}
          <h2 className="nt-card-title">{title}</h2>
          {actions}
        </header>
      )}
      {padding ? <div className="nt-card-body">{children}</div> : children}
    </section>
  )
}
