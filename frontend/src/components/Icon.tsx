import type * as React from 'react'
import { ICON_PATHS } from './iconPaths'


export type IconName = keyof typeof ICON_PATHS

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  name: IconName
  size?: number
  title?: string
  strokeWidth?: number
}

export function Icon({ name, size = 16, title, strokeWidth = 1.75, className, ...rest }: IconProps) {
  const a11y = title ? { role: 'img', 'aria-label': title } : { 'aria-hidden': true }
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={['nt-icon', className].filter(Boolean).join(' ')}
      focusable="false"
      {...a11y}
      {...rest}
    >
      {title && <title>{title}</title>}
      <path d={ICON_PATHS[name]} />
    </svg>
  )
}

Icon.names = Object.keys(ICON_PATHS) as IconName[]
