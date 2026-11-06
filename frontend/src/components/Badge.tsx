import type * as React from 'react'
import { Icon, type IconName } from './Icon'

export type Tone = 'neutral' | 'accent' | 'secondary' | 'success' | 'warning' | 'danger'

export interface BadgeProps {
  tone?: Tone
  icon?: IconName
  children?: React.ReactNode
}

export function Badge({ tone = 'neutral', icon, children }: BadgeProps) {
  return (
    <span className={tone === 'neutral' ? 'nt-badge' : `nt-badge nt-badge-${tone}`}>
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  )
}
