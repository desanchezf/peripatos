import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '../../api/client'
import type { QuizSummary } from '../../api/types'
import { Badge, Card, EmptyState, Loading } from '../../components'

export default function QuizzesPage() {
  const { data, isPending, error } = useQuery({ queryKey: ['quizzes'], queryFn: () => api<QuizSummary[]>('/api/quizzes/quizzes/') })
  const [selected, setSelected] = useState<number | null>(null)
  if (error) throw error
  if (isPending) return <Loading />

  const topics = new Map<number | null, { name: string; description: string; quizzes: QuizSummary[] }>()
  for (const quiz of data) {
    const id = quiz.topic?.id ?? null
    if (!topics.has(id)) topics.set(id, { name: quiz.topic?.name ?? 'Sin tema', description: quiz.topic?.description ?? '', quizzes: [] })
    topics.get(id)!.quizzes.push(quiz)
  }
  const groups = [...topics.entries()].filter(([id]) => selected === null || id === selected)

  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <h1 className="t-title-1">Cuestionarios</h1>
          <p className="nt-muted">Practica por tema y repite cuando quieras.</p>
        </div>
        {topics.size > 1 && (
          <div className="nt-segmented" role="group" aria-label="Filtrar por tema">
            <button type="button" aria-pressed={selected === null} onClick={() => setSelected(null)}>Todos</button>
            {[...topics.entries()].map(([id, topic]) => (
              <button key={id ?? 'none'} type="button" aria-pressed={selected === id} onClick={() => setSelected(id)}>{topic.name}</button>
            ))}
          </div>
        )}
      </header>
      {data.length === 0 && <EmptyState icon="task" title="Aún no hay cuestionarios" adminPath="/admin/quizzes/quiz/add/" />}
      {groups.map(([id, topic]) => (
        <Card key={id ?? 'none'} title={topic.name} icon="task" padding={false} actions={<span className="nt-nav-count">{topic.quizzes.length}</span>}>
          {topic.description && <p className="pt-card-note nt-muted">{topic.description}</p>}
          <ul className="pt-list">
            {topic.quizzes.map((quiz) => (
              <li key={quiz.id}>
                <Link className="pt-row pt-row-link" to={`/quizzes/${quiz.id}`}>
                  <span className="nt-grow nt-ellipsis">{quiz.title}</span>
                  <span className="pt-row-meta nt-muted">{quiz.question_count} preguntas</span>
                  {quiz.best_percent === null
                    ? <Badge>Pendiente</Badge>
                    : <Badge tone={quiz.best_percent >= 50 ? 'success' : 'warning'} icon={quiz.best_percent >= 50 ? 'check' : 'alert'}>Mejor nota: {quiz.best_percent} %</Badge>}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  )
}
