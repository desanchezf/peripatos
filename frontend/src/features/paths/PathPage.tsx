import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { api } from '../../api/client'
import type { NodeStatus, PathDetail, PathNode } from '../../api/types'
import { Badge, Button, Icon, IconButton, Loading, Markdown, type IconName } from '../../components'
import { errorText } from '../../lib/format'

const STATUS: { id: NodeStatus; label: string; icon: IconName }[] = [
  { id: 'pending', label: 'Pendiente', icon: 'minus' },
  { id: 'in_progress', label: 'En curso', icon: 'clock' },
  { id: 'done', label: 'Hecho', icon: 'check' },
  { id: 'skipped', label: 'Omitir', icon: 'x' },
]
const STATUS_ICON: Partial<Record<NodeStatus, IconName>> = { in_progress: 'clock', done: 'check', skipped: 'x' }
const KINDS = [
  { id: 'core', label: 'Imprescindible' },
  { id: 'recommended', label: 'Recomendado' },
  { id: 'alternative', label: 'Alternativa' },
  { id: 'optional', label: 'Opcional' },
]

function NodeButton({ node, onOpen }: { node: PathNode; onOpen: () => void }) {
  const icon = STATUS_ICON[node.status]
  const state = STATUS.find((item) => item.id === node.status)!.label
  return (
    <button type="button" className={`pt-node pt-node-${node.kind} pt-node-is-${node.status}`} onClick={onOpen} title={`${node.kind_label} · ${state}`}>
      {icon && <Icon name={icon} size={14} />}
      <span className="pt-node-title">{node.title}</span>
      <span className="nt-sr-only">({node.kind_label}, {state})</span>
    </button>
  )
}

export default function PathPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const key = ['path', id]
  const { data: path, isPending, error } = useQuery({ queryKey: key, queryFn: () => api<PathDetail>(`/api/roadmap/paths/${id}/`) })
  const [openId, setOpenId] = useState<number | null>(null)

  const enrollment = useMutation({
    mutationFn: (join: boolean) => api<PathDetail>(`/api/roadmap/paths/${id}/enrollment/`, { method: join ? 'POST' : 'DELETE' }),
    onSuccess: (updated) => {
      queryClient.setQueryData(key, updated)
      queryClient.invalidateQueries({ queryKey: ['paths'] })
    },
  })
  const setStatus = useMutation({
    mutationFn: ({ nodeId, status }: { nodeId: number; status: NodeStatus }) =>
      api(`/api/roadmap/nodes/${nodeId}/progress/`, { method: 'PUT', json: { status } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: key })
      queryClient.invalidateQueries({ queryKey: ['paths'] })
    },
  })

  useEffect(() => {
    if (openId === null) return
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpenId(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [openId])

  if (error) throw error
  if (isPending) return <Loading />

  const open = path.stages.flatMap((stage) => stage.nodes).find((node) => node.id === openId) ?? null

  return (
    <div className="nt-page nt-page-wide">
      <header className="nt-page-head">
        <div>
          <Link to="/paths" className="pt-back"><Icon name="chevron-left" size={14} />Trayectorias</Link>
          <h1 className="t-title-1">{path.title}</h1>
          {path.summary && <p className="nt-muted">{path.summary}</p>}
        </div>
        {path.enrolled
          ? (
            <div className="nt-toolbar">
              <span className="pt-path-progress">
                <span className="nt-muted">{path.done_nodes} de {path.node_count} · {path.percent} %</span>
                <progress className="nt-progress" value={path.percent} max={100} aria-label={`Avance: ${path.percent} %`} />
              </span>
              <Button size="sm" variant="ghost" disabled={enrollment.isPending} onClick={() => enrollment.mutate(false)}>Dejar de seguir</Button>
            </div>
          )
          : <Button variant="primary" icon="check" disabled={enrollment.isPending} onClick={() => enrollment.mutate(true)}>Elegir esta trayectoria</Button>}
      </header>

      {path.description && <Markdown>{path.description}</Markdown>}

      <ul className="pt-legend" aria-label="Leyenda">
        {KINDS.map((kind) => <li key={kind.id}><span className={`pt-legend-sw pt-node-${kind.id}`} aria-hidden />{kind.label}</li>)}
      </ul>

      {path.stages.length === 0
        ? <p className="nt-muted">Esta trayectoria aún no tiene etapas.</p>
        : (
          <div className="pt-map">
            {path.stages.map((stage) => (
              <section key={stage.id} className="pt-stage" aria-label={stage.title}>
                <div className="pt-branch pt-branch-left">
                  {stage.nodes.filter((_, index) => index % 2 === 0).map((node) => <NodeButton key={node.id} node={node} onOpen={() => setOpenId(node.id)} />)}
                </div>
                <div className="pt-stage-title" title={stage.description}>{stage.title}</div>
                <div className="pt-branch pt-branch-right">
                  {stage.nodes.filter((_, index) => index % 2 === 1).map((node) => <NodeButton key={node.id} node={node} onOpen={() => setOpenId(node.id)} />)}
                </div>
              </section>
            ))}
          </div>
        )}

      {open && (
        <>
          <div className="pt-drawer-scrim" onClick={() => setOpenId(null)} aria-hidden />
          <aside className="pt-drawer" role="dialog" aria-modal="true" aria-label={open.title}>
            <header className="pt-drawer-head">
              <h2 className="t-title-3 nt-grow">{open.title}</h2>
              <IconButton icon="x" label="Cerrar" autoFocus onClick={() => setOpenId(null)} />
            </header>
            <Badge tone={open.kind === 'core' ? 'accent' : open.kind === 'optional' ? 'neutral' : 'secondary'}>{open.kind_label}</Badge>

            {path.enrolled
              ? (
                <div className="nt-segmented" role="group" aria-label="Tu estado en este tema">
                  {STATUS.map((status) => (
                    <button key={status.id} type="button" aria-pressed={open.status === status.id} disabled={setStatus.isPending} onClick={() => setStatus.mutate({ nodeId: open.id, status: status.id })}>
                      <Icon name={status.icon} size={14} />{status.label}
                    </button>
                  ))}
                </div>
              )
              : <p className="nt-muted">Elige esta trayectoria para registrar tu avance.</p>}
            {setStatus.error && <p className="pt-error" role="alert">{errorText(setStatus.error) || 'No se pudo guardar'}</p>}

            {open.description ? <Markdown>{open.description}</Markdown> : <p className="nt-muted">Este tema aún no tiene descripción.</p>}

            {(open.links.length > 0 || open.resource_url) && (
              <div className="pt-drawer-links">
                <h3 className="t-title-3">Para aprenderlo</h3>
                {open.links.map((link) => <Link key={link.to} to={link.to}>{link.title}</Link>)}
                {open.resource_url && <a href={open.resource_url} target="_blank" rel="noopener noreferrer">Recurso externo <Icon name="external" size={14} /></a>}
              </div>
            )}
          </aside>
        </>
      )}
    </div>
  )
}
