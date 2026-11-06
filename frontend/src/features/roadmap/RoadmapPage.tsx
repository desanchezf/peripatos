import { useQuery } from '@tanstack/react-query'
import { Link, Navigate, useParams } from 'react-router'
import { api } from '../../api/client'
import type { StepType, Training } from '../../api/types'
import { Badge, EmptyState, Icon, Loading, Markdown, type IconName } from '../../components'
import { formatDay } from '../../lib/format'

const STEP: Record<StepType, { icon: IconName; label: string; path: string }> = {
  reading: { icon: 'book', label: 'Lectura', path: '/readings' },
  quiz: { icon: 'task', label: 'Cuestionario', path: '/quizzes' },
  lab: { icon: 'flask', label: 'Laboratorio', path: '/labs' },
}

export default function RoadmapPage() {
  const { id } = useParams()
  const { data, isPending, error } = useQuery({ queryKey: ['trainings'], queryFn: () => api<Training[]>('/api/roadmap/trainings/') })
  if (error) throw error
  if (isPending) return <Loading />

  if (data.length === 0) {
    return (
      <div className="nt-page">
        <h1 className="t-title-1">Roadmap</h1>
        <EmptyState icon="route" title="Aún no hay formaciones" adminPath="/admin/roadmap/training/add/">Cada formación tendrá aquí su propio roadmap.</EmptyState>
      </div>
    )
  }
  if (!id) return <Navigate to={`/roadmap/${data[0].id}`} replace />
  const training = data.find((item) => String(item.id) === id)
  if (!training) return <EmptyState icon="alert" title="Esta formación no existe" />

  const nextStep = training.steps.find((step) => !step.done)
  return (
    <div className="nt-page nt-page-wide pt-roadmap">
      <h1 className="t-title-1">Roadmap</h1>
      <div className="pt-roadmap-layout">
        <nav className="pt-training-list" aria-label="Formaciones">
          {data.map((item) => (
            <Link key={item.id} to={`/roadmap/${item.id}`} className="pt-training" aria-current={item.id === training.id ? 'page' : undefined}>
              <span className="pt-training-title">{item.title}</span>
              <span className="nt-muted pt-row-meta">{item.done_steps} de {item.total_steps} pasos</span>
              <progress className="nt-progress" value={item.percent} max={100} aria-label={`${item.title}: ${item.percent} %`} />
            </Link>
          ))}
        </nav>

        <section className="pt-training-detail">
          <header>
            <h2 className="t-title-2">{training.title}</h2>
            <p className="nt-muted">
              {training.percent} % completado
              {training.target_date && ` · Objetivo: ${formatDay(training.target_date)}`}
            </p>
            {training.description && <Markdown>{training.description}</Markdown>}
          </header>

          {training.steps.length === 0
            ? <EmptyState icon="route" title="Esta formación aún no tiene pasos" adminPath={`/admin/roadmap/training/${training.id}/change/`} />
            : (
              <ol className="pt-timeline">
                {training.steps.map((step) => {
                  const kind = STEP[step.type]
                  const isNext = step === nextStep
                  return (
                    <li key={step.id} className={['pt-step', step.done && 'pt-step-done', isNext && 'pt-step-next'].filter(Boolean).join(' ')}>
                      <span className="pt-step-mark" aria-hidden><Icon name={step.done ? 'check' : kind.icon} size={16} /></span>
                      <Link to={`${kind.path}/${step.item_id}`} className="pt-step-body">
                        <span className="pt-row-meta nt-muted">{kind.label}</span>
                        <span className="pt-step-title">{step.title}</span>
                      </Link>
                      {step.done && <Badge tone="success" icon="check">Hecho</Badge>}
                      {isNext && <Badge tone="accent" icon="chevron-right">Siguiente</Badge>}
                    </li>
                  )
                })}
              </ol>
            )}
        </section>
      </div>
    </div>
  )
}
