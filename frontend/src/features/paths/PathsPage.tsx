import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { api } from '../../api/client'
import type { PathSummary } from '../../api/types'
import { Badge, EmptyState, Icon, Loading } from '../../components'

function PathCard({ path }: { path: PathSummary }) {
  return (
    <Link to={`/paths/${path.id}`} className="pt-pathcard">
      <span className="pt-pathcard-head">
        <Icon name="graph" size={18} />
        <strong className="nt-grow">{path.title}</strong>
        {path.enrolled && <Badge tone="accent" icon="check">Elegida</Badge>}
      </span>
      {path.summary && <span className="nt-muted">{path.summary}</span>}
      <span className="pt-row-meta nt-muted">{path.stage_count} etapas · {path.node_count} temas</span>
      {path.enrolled && <progress className="nt-progress" value={path.percent} max={100} aria-label={`Avance: ${path.percent} %`} />}
    </Link>
  )
}

export default function PathsPage() {
  const { data, isPending, error } = useQuery({ queryKey: ['paths'], queryFn: () => api<PathSummary[]>('/api/roadmap/paths/') })
  if (error) throw error
  if (isPending) return <Loading />
  const mine = data.filter((path) => path.enrolled)
  const others = data.filter((path) => !path.enrolled)
  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <h1 className="t-title-1">Trayectorias</h1>
          <p className="nt-muted">Elige hacia dónde quieres crecer y sigue su mapa de temas.</p>
        </div>
      </header>
      {data.length === 0 && <EmptyState icon="graph" title="Aún no hay trayectorias" adminPath="/admin/roadmap/careerpath/add/" />}
      {mine.length > 0 && (
        <section className="pt-paths-section">
          <h2 className="t-title-3">Tus trayectorias</h2>
          <div className="pt-pathgrid">{mine.map((path) => <PathCard key={path.id} path={path} />)}</div>
        </section>
      )}
      {others.length > 0 && (
        <section className="pt-paths-section">
          <h2 className="t-title-3">{mine.length > 0 ? 'Otras trayectorias' : 'Elige tu trayectoria'}</h2>
          <div className="pt-pathgrid">{others.map((path) => <PathCard key={path.id} path={path} />)}</div>
        </section>
      )}
    </div>
  )
}
