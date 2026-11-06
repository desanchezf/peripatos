import type * as React from 'react'
import { Icon, type IconName } from './Icon'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'md' | 'sm'
  icon?: IconName
  iconRight?: IconName
}

export function Button({ variant = 'secondary', size = 'md', icon, iconRight, className, type = 'button', children, ...rest }: ButtonProps) {
  const classes = ['nt-btn', variant !== 'secondary' && `nt-btn-${variant}`, size === 'sm' && 'nt-btn-sm', className]
  const iconSize = size === 'sm' ? 14 : 16
  return (
    <button type={type} className={classes.filter(Boolean).join(' ')} {...rest}>
      {icon && <Icon name={icon} size={iconSize} />}
      {children}
      {iconRight && <Icon name={iconRight} size={iconSize} />}
    </button>
  )
}
