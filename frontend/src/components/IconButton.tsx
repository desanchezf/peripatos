import type * as React from 'react'
import { Icon, type IconName } from './Icon'

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: IconName
  /** aria-label y tooltip */
  label: string
  variant?: 'ghost' | 'outline' | 'primary'
  /** Tamaño del icono en px */
  size?: number
}

export function IconButton({ icon, label, variant = 'ghost', size = 16, className, type = 'button', ...rest }: IconButtonProps) {
  const classes = ['nt-iconbtn', variant !== 'ghost' && `nt-iconbtn-${variant}`, className]
  return (
    <button type={type} className={classes.filter(Boolean).join(' ')} aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={size} />
    </button>
  )
}
