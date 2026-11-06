import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { api } from '../../api/client'
import type { QuizDetail, QuizResult } from '../../api/types'
import { Badge, Button, Card, EmptyState, Icon, Loading } from '../../components'
import { errorText } from '../../lib/format'

export default function QuizPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const { data: quiz, isPending, error } = useQuery({ queryKey: ['quiz', id], queryFn: () => api<QuizDetail>(`/api/quizzes/quizzes/${id}/`) })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const submit = useMutation({
    mutationFn: () => api<QuizResult>(`/api/quizzes/quizzes/${id}/submit/`, { method: 'POST', json: { answers } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
      queryClient.invalidateQueries({ queryKey: ['quiz', id] })
      document.getElementById('nt-main')?.scrollTo({ top: 0 })
    },
  })

  if (error) throw error
  if (isPending) return <Loading />

  const result = submit.data
  const resultOf = (questionId: number) => result?.results.find((item) => item.question === questionId)
  const answered = Object.keys(answers).length
  const restart = () => {
    setAnswers({})
    submit.reset()
    document.getElementById('nt-main')?.scrollTo({ top: 0 })
  }

  return (
    <div className="nt-page">
      <header>
        <Link to="/quizzes" className="pt-back"><Icon name="chevron-left" size={14} />Cuestionarios</Link>
        <h1 className="t-title-1">{quiz.title}</h1>
        {quiz.topic && <p className="nt-muted">{quiz.topic.name}</p>}
        {quiz.description && <p>{quiz.description}</p>}
      </header>

      {quiz.questions.length === 0 && <EmptyState icon="task" title="Este cuestionario aún no tiene preguntas" />}

      {result && (
        <div className="pt-score" role="status">
          <strong className="pt-metric-value">{result.percent} %</strong>
          <span>{result.score} de {result.total} aciertos</span>
          <Button icon="refresh" onClick={restart}>Repetir</Button>
        </div>
      )}

      {quiz.questions.map((question, index) => {
        const outcome = resultOf(question.id)
        return (
          <Card key={question.id} title={`Pregunta ${index + 1}`} actions={outcome && (
            outcome.correct ? <Badge tone="success" icon="check">Correcta</Badge> : <Badge tone="danger" icon="x">{outcome.selected === null ? 'Sin responder' : 'Incorrecta'}</Badge>
          )}>
            <fieldset className="pt-question" disabled={Boolean(result)}>
              <legend className="pt-question-text">{question.text}</legend>
              {question.choices.map((choice) => {
                const isCorrect = outcome?.correct_choices.includes(choice.id)
                const isWrong = outcome && outcome.selected === choice.id && !isCorrect
                return (
                  <label key={choice.id} className={['pt-choice', isCorrect && 'pt-choice-right', isWrong && 'pt-choice-wrong'].filter(Boolean).join(' ')}>
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      checked={answers[question.id] === choice.id}
                      onChange={() => setAnswers({ ...answers, [question.id]: choice.id })}
                    />
                    <span className="nt-grow">{choice.text}</span>
                    {isCorrect && <Icon name="check" size={16} title="Respuesta correcta" />}
                    {isWrong && <Icon name="x" size={16} title="Tu respuesta" />}
                  </label>
                )
              })}
            </fieldset>
            {outcome?.explanation && <p className="pt-explanation"><strong>Explicación:</strong> {outcome.explanation}</p>}
          </Card>
        )
      })}

      {!result && quiz.questions.length > 0 && (
        <div className="pt-submitbar">
          <span className="nt-muted" aria-live="polite">{answered} de {quiz.questions.length} respondidas</span>
          {submit.error && <span className="pt-error" role="alert">{errorText(submit.error) || 'No se pudo enviar'}</span>}
          <Button variant="primary" disabled={answered < quiz.questions.length || submit.isPending} onClick={() => submit.mutate()}>Corregir</Button>
        </div>
      )}
    </div>
  )
}
