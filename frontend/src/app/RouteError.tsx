import { Link, useRouteError } from 'react-router'
import { Icon } from '../components'

export function NotFound() {
  return (
    <div className="nt-empty">
      <Icon name="alert" size={32} />
      <h1 className="t-title-2">Esta página no existe</h1>
      <p className="nt-muted">Revisa la dirección o vuelve al <Link to="/">panel</Link>.</p>
    </div>
  )
}

export function RouteError() {
  const error = useRouteError()
  return (
    <div className="nt-empty" role="alert">
      <Icon name="alert" size={32} />
      <h1 className="t-title-2">Algo ha fallado</h1>
      <p className="nt-muted">{error instanceof Error ? error.message : 'No se pudo cargar esta vista.'}</p>
      <Link to="/">Volver al panel</Link>
    </div>
  )
}
