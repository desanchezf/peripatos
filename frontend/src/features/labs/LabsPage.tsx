import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { api } from '../../api/client'
import type { Lab } from '../../api/types'
import { Badge, Card, EmptyState, Loading } from '../../components'
import { formatDay } from '../../lib/format'

export function LabStatus({ lab }: { lab: Lab }) {
  const latest = lab.submissions[0]
  if (!latest) return <Badge>Sin entregar</Badge>
  return latest.status === 'reviewed'
    ? <Badge tone="success" icon="check">{latest.status_label}</Badge>
    : <Badge tone="secondary" icon="upload">{latest.status_label}</Badge>
}

export default function LabsPage() {
  const { data, isPending, error } = useQuery({ queryKey: ['labs'], queryFn: () => api<Lab[]>('/api/labs/labs/') })
  if (error) throw error
  if (isPending) return <Loading />
  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <h1 className="t-title-1">Laboratorios</h1>
          <p className="nt-muted">Lee el enunciado y la teoría, y sube tu solución.</p>
        </div>
      </header>
      {data.length === 0
        ? <EmptyState icon="flask" title="Aún no hay laboratorios" adminPath="/admin/labs/lab/add/" />
        : (
          <Card padding={false}>
            <ul className="pt-list">
              {data.map((lab) => (
                <li key={lab.id}>
                  <Link className="pt-row pt-row-link" to={`/labs/${lab.id}`}>
                    <span className="nt-grow nt-ellipsis">{lab.title}</span>
                    {lab.due_date && <span className="pt-row-meta nt-muted">Hasta el {formatDay(lab.due_date)}</span>}
                    <LabStatus lab={lab} />
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        )}
    </div>
  )
}
