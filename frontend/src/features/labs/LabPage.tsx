import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router'
import { api } from '../../api/client'
import type { Lab } from '../../api/types'
import { Badge, Button, Card, Icon, Loading, Markdown, TextField } from '../../components'
import { errorText, formatDay, formatSize } from '../../lib/format'
import { LabStatus } from './LabsPage'

const MAX_SIZE = 25 * 1024 * 1024

export default function LabPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const { data: lab, isPending, error } = useQuery({ queryKey: ['lab', id], queryFn: () => api<Lab>(`/api/labs/labs/${id}/`) })
  const [tab, setTab] = useState<'statement' | 'theory'>('statement')
  const [file, setFile] = useState<File | null>(null)
  const [comment, setComment] = useState('')
  const input = useRef<HTMLInputElement>(null)

  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('lab', String(id))
      form.append('file', file!)
      form.append('comment', comment)
      return api('/api/labs/submissions/', { method: 'POST', body: form })
    },
    onSuccess: () => {
      setFile(null)
      setComment('')
      if (input.current) input.current.value = ''
      queryClient.invalidateQueries({ queryKey: ['lab', id] })
      queryClient.invalidateQueries({ queryKey: ['labs'] })
    },
  })

  if (error) throw error
  if (isPending) return <Loading />

  const tooBig = Boolean(file && file.size > MAX_SIZE)
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (file && !tooBig) upload.mutate()
  }
  const uploadError = tooBig ? 'La solución no puede superar los 25 MB.' : upload.error ? errorText(upload.error) || 'No se pudo subir la solución' : ''

  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <Link to="/labs" className="pt-back"><Icon name="chevron-left" size={14} />Laboratorios</Link>
          <h1 className="t-title-1">{lab.title}</h1>
          {lab.due_date && <p className="nt-muted">Fecha límite: {formatDay(lab.due_date)}</p>}
        </div>
        <LabStatus lab={lab} />
      </header>

      <div className="pt-lab">
        <section className="pt-lab-main">
          <div className="nt-segmented" role="group" aria-label="Contenido del laboratorio">
            <button type="button" aria-pressed={tab === 'statement'} onClick={() => setTab('statement')}>Enunciado</button>
            <button type="button" aria-pressed={tab === 'theory'} onClick={() => setTab('theory')}>Teoría</button>
          </div>
          <Card>
            {(tab === 'statement' ? lab.statement : lab.theory)
              ? <Markdown>{tab === 'statement' ? lab.statement : lab.theory}</Markdown>
              : <p className="nt-muted">{tab === 'statement' ? 'Este laboratorio aún no tiene enunciado.' : 'Este laboratorio no incluye teoría.'}</p>}
          </Card>
        </section>

        <aside className="pt-lab-side">
          <Card title="Entregar solución" icon="upload">
            <form className="nt-form" onSubmit={submit}>
              <div className="nt-field">
                <label className="nt-field-label" htmlFor="pt-solution">Fichero (máx. 25 MB)</label>
                <input id="pt-solution" ref={input} className="nt-field-control" type="file" required onChange={(e) => { upload.reset(); setFile(e.target.files?.[0] ?? null) }} />
                {file && <span className="nt-field-hint">{file.name} · {formatSize(file.size)}</span>}
              </div>
              <TextField label="Comentario (opcional)" multiline rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
              {uploadError && <p className="pt-error" role="alert">{uploadError}</p>}
              <Button variant="primary" type="submit" icon="upload" disabled={!file || tooBig || upload.isPending}>{upload.isPending ? 'Subiendo…' : 'Subir solución'}</Button>
            </form>
          </Card>

          {lab.submissions.length > 0 && (
            <Card title="Tus entregas" icon="file" padding={false} actions={<span className="nt-nav-count">{lab.submissions.length}</span>}>
              <ul className="pt-list">
                {lab.submissions.map((submission) => (
                  <li key={submission.id} className="pt-submission">
                    <div className="pt-row">
                      <a className="nt-grow nt-ellipsis" href={submission.file_url} title={submission.file_name}><Icon name="download" size={14} /> {submission.file_name}</a>
                      <Badge tone={submission.status === 'reviewed' ? 'success' : 'secondary'}>{submission.status_label}</Badge>
                    </div>
                    <p className="pt-row-meta nt-muted">{formatDay(submission.submitted_at)}{submission.comment ? ` · ${submission.comment}` : ''}</p>
                    {submission.feedback && <p className="pt-explanation"><strong>Revisión:</strong> {submission.feedback}</p>}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </aside>
      </div>
    </div>
  )
}
