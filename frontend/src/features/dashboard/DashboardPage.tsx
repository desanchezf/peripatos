import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { api } from '../../api/client'
import type { Dashboard } from '../../api/types'
import { Badge, Card, Icon, IconButton, Loading, type IconName } from '../../components'

function Metric({ to, icon, label, value, detail, percent, className }: {
  to: string
  icon: IconName
  label: string
  value: ReactNode
  detail: string
  percent?: number
  className: string
}) {
  return (
    <Link to={to} className={`pt-metric ${className}`}>
      <span className="pt-metric-label"><Icon name={icon} size={16} />{label}</span>
      <strong className="pt-metric-value">{value}</strong>
      <span className="pt-metric-detail nt-muted">{detail}</span>
      {percent !== undefined && <progress className="nt-progress" value={percent} max={100} aria-label={`${label}: ${percent} %`} />}
    </Link>
  )
}

function PendingList<T extends { id: number | string }>({ title, icon, items, empty, render }: {
  title: string
  icon: IconName
  items: T[]
  empty: string
  render: (item: T) => ReactNode
}) {
  return (
    <Card title={title} icon={icon} padding={false} actions={<span className="nt-nav-count">{items.length}</span>}>
      {items.length === 0
        ? <p className="pt-list-empty nt-muted">{empty}</p>
        : <ul className="pt-list">{items.map((item) => <li key={item.id}>{render(item)}</li>)}</ul>}
    </Card>
  )
}

export default function DashboardPage() {
  const queryClient = useQueryClient()
  const { data, isPending, error } = useQuery({ queryKey: ['dashboard'], queryFn: () => api<Dashboard>('/api/dashboard/') })
  const dismiss = useMutation({
    mutationFn: (id: number) => api(`/api/dashboard/notices/${id}/dismiss/`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
  })

  if (error) throw error
  if (isPending) return <Loading />
  const { metrics } = data
  const readPercent = metrics.readings.total ? Math.round((100 * metrics.readings.finished) / metrics.readings.total) : 0

  return (
    <div className="pt-dash">
      <h1 className="nt-sr-only">Panel</h1>
      <section className="pt-bento" aria-label="Métricas">
        <Metric
          to="/readings" icon="book" label="Lecturas pendientes" className="pt-m-readings"
          value={metrics.readings.pending}
          detail={`${metrics.readings.in_progress} en curso · ${metrics.readings.finished} de ${metrics.readings.total} terminadas`}
          percent={readPercent}
        />
        <Metric
          to="/roadmap" icon="route" label="Formaciones pendientes" className="pt-m-trainings"
          value={metrics.trainings.pending}
          detail={`de ${metrics.trainings.total} · ${metrics.trainings.percent} % de los pasos completados`}
          percent={metrics.trainings.percent}
        />
        <Metric
          to="/quizzes" icon="task" label="Cuestionarios pendientes" className="pt-m-quizzes"
          value={metrics.quizzes.pending} detail={`de ${metrics.quizzes.total}`}
        />
        <Metric
          to="/labs" icon="flask" label="Laboratorios pendientes" className="pt-m-labs"
          value={metrics.labs.pending} detail={`de ${metrics.labs.total}`}
        />
        <Metric
          to="/quizzes" icon="check" label="Nota media" className="pt-m-score"
          value={metrics.average_score === null ? '—' : `${metrics.average_score} %`}
          detail={metrics.average_score === null ? 'Aún sin intentos' : 'En todos tus intentos'}
        />
      </section>

      <section className="pt-dash-lists" aria-label="Pendiente">
        <PendingList
          title="Avisos" icon="alert" items={data.notices} empty="Sin avisos."
          render={(notice) => (
            <div className="pt-row">
              <div className="nt-grow">
                {notice.link ? <Link to={notice.link}>{notice.title}</Link> : <strong className="pt-row-title">{notice.title}</strong>}
                {notice.body && <p className="pt-row-meta nt-muted">{notice.body}</p>}
              </div>
              {notice.level === 'warning' && <Badge tone="warning" icon="alert">Importante</Badge>}
              {notice.notice_id !== null && (
                <IconButton icon="x" label="Descartar aviso" disabled={dismiss.isPending} onClick={() => dismiss.mutate(notice.notice_id!)} />
              )}
            </div>
          )}
        />
        <PendingList
          title="Cuestionarios pendientes" icon="task" items={data.pending_quizzes} empty="Ningún cuestionario pendiente."
          render={(quiz) => (
            <Link className="pt-row pt-row-link" to={`/quizzes/${quiz.id}`}>
              <span className="nt-grow nt-ellipsis">{quiz.title}</span>
              <span className="pt-row-meta nt-muted">{quiz.topic ?? 'Sin tema'} · {quiz.question_count} preg.</span>
            </Link>
          )}
        />
        <PendingList
          title="Lecturas pendientes" icon="book" items={data.pending_readings} empty="Ninguna lectura pendiente."
          render={(reading) => (
            <Link className="pt-row pt-row-link" to={`/readings/${reading.id}`}>
              <span className="nt-grow nt-ellipsis">{reading.title}</span>
              <span className="pt-row-meta nt-muted">{reading.percent > 0 ? `${Math.round(reading.percent)} %` : reading.kind_label}</span>
            </Link>
          )}
        />
      </section>
    </div>
  )
}
