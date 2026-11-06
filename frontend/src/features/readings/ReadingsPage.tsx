import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { api } from '../../api/client'
import type { Material } from '../../api/types'
import { Badge, Card, EmptyState, Loading } from '../../components'

const FORMAT_LABEL = { pdf: 'PDF', epub: 'EPUB', text: 'Texto' }

export default function ReadingsPage() {
  const { data, isPending, error } = useQuery({ queryKey: ['materials'], queryFn: () => api<Material[]>('/api/theory/materials/') })
  if (error) throw error
  if (isPending) return <Loading />

  const inProgress = data.filter((m) => !m.progress.finished && m.progress.percent > 0)
  const pending = data.filter((m) => !m.progress.finished && m.progress.percent === 0)
  const finished = data.filter((m) => m.progress.finished)
  const groups = [
    { title: 'Seguir leyendo', items: inProgress },
    { title: 'Pendientes', items: pending },
    { title: 'Terminadas', items: finished },
  ].filter((group) => group.items.length > 0)

  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <h1 className="t-title-1">Lecturas</h1>
          <p className="nt-muted">Teoría y libros, y continúa siempre por donde ibas.</p>
        </div>
      </header>
      {data.length === 0 && <EmptyState icon="book" title="Aún no hay lecturas" adminPath="/admin/theory/material/add/" />}
      {groups.map((group) => (
        <Card key={group.title} title={group.title} padding={false} actions={<span className="nt-nav-count">{group.items.length}</span>}>
          <ul className="pt-list">
            {group.items.map((material) => (
              <li key={material.id}>
                <Link className="pt-row pt-row-link" to={`/readings/${material.id}`}>
                  <span className="nt-grow nt-ellipsis">{material.title}</span>
                  <Badge>{FORMAT_LABEL[material.format] ?? material.format}</Badge>
                  <Badge tone="secondary">{material.kind_label}</Badge>
                  {!material.progress.finished && material.progress.percent > 0 && (
                    <progress className="nt-progress pt-row-progress" value={material.progress.percent} max={100} aria-label={`${Math.round(material.progress.percent)} % leído`} />
                  )}
                  {material.progress.finished && <Badge tone="success" icon="check">Leída</Badge>}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  )
}
