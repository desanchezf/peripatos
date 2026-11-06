import { useId } from 'react'
import type * as React from 'react'
import { Icon, type IconName } from './Icon'

export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  hint?: string
  /** Sustituye a la ayuda y marca el borde en danger */
  error?: string
  icon?: IconName
  multiline?: boolean
  rows?: number
}

export function TextField({ label, hint, error, icon, multiline, rows = 3, id, className, ...rest }: TextFieldProps) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const help = error ?? hint
  const helpId = help ? `${fieldId}-help` : undefined
  const common = {
    id: fieldId,
    className: 'nt-field-control',
    'aria-invalid': error ? true : undefined,
    'aria-describedby': helpId,
  }
  return (
    <div className={['nt-field', error && 'nt-field-error', className].filter(Boolean).join(' ')}>
      {label && <label className="nt-field-label" htmlFor={fieldId}>{label}</label>}
      <div className="nt-field-wrap">
        {icon && <Icon name={icon} size={16} />}
        {multiline ? (
          <textarea {...(rest as unknown as React.TextareaHTMLAttributes<HTMLTextAreaElement>)} {...common} rows={rows} />
        ) : (
          <input {...rest} {...common} />
        )}
      </div>
      {help && <span id={helpId} className="nt-field-hint">{help}</span>}
    </div>
  )
}
