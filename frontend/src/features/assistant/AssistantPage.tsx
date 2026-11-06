import type { ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, ApiError } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import type { Conversation } from '../../api/types'
import { Button, EmptyState, Icon, IconButton, Loading, Markdown, NavItem, TextField } from '../../components'
import { useChat } from './useChat'

type Chat = ReturnType<typeof useChat>

function Bubble({ role, model, children }: { role: 'user' | 'assistant' | 'system'; model?: string; children: ReactNode }) {
  return (
    <div className={`nt-msg nt-msg-${role}`}>
      {role !== 'system' && (
        <div className="nt-msg-head">
          {role === 'assistant' && <span className="nt-msg-avatar"><Icon name="spark" size={12} /></span>}
          <strong>{role === 'user' ? 'Tú' : 'Asistente'}</strong>
          {role === 'assistant' && model && <span>{model}</span>}
        </div>
      )}
      <div className="nt-msg-bubble">{children}</div>
    </div>
  )
}

function Messages({ chat }: { chat: Chat }) {
  const bottom = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' })
  }, [chat.messages.length, chat.pending])

  return (
    <div className="nt-ws-chat" aria-live="polite" aria-busy={chat.streaming}>
      {chat.messages.length === 0 && !chat.pending && <Bubble role="system">Pregunta lo que quieras: dudas de una lectura, un concepto, un laboratorio…</Bubble>}
      {chat.messages.map((m) => (
        <Bubble key={m.id} role={m.role} model={chat.modelLabel(m.model)}>
          {m.role === 'user' ? m.content : <Markdown>{m.content}</Markdown>}
        </Bubble>
      ))}
      {chat.pending && (
        <>
          <Bubble role="user">{chat.pending.user}</Bubble>
          {(chat.pending.content || chat.streaming) && (
            <Bubble role="assistant" model={chat.modelLabel(chat.selectedModel ?? null)}>
              {chat.pending.content ? <Markdown>{chat.pending.content}</Markdown> : <span className="nt-muted">Pensando…</span>}
            </Bubble>
          )}
          {chat.pending.error && <Bubble role="system"><span className="nt-inline-error" role="alert">{chat.pending.error}</span></Bubble>}
        </>
      )}
      <div ref={bottom} />
    </div>
  )
}

/** Intro envía, Mayús+Intro salta de línea */
function Composer({ chat }: { chat: Chat }) {
  const [input, setInput] = useState('')

  const submit = async (event?: FormEvent) => {
    event?.preventDefault()
    const text = input.trim()
    if (!text || chat.streaming || !chat.selectedModel) return
    setInput('')
    if (!(await chat.send(text))) setInput(text)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form className="nt-ws-compose" onSubmit={submit}>
      <TextField
        multiline
        rows={2}
        className="pt-assistant-field"
        aria-label="Mensaje para el asistente"
        placeholder="Escribe tu pregunta"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
        autoFocus
      />
      {chat.streaming ? (
        <IconButton icon="stop" variant="outline" label="Parar la respuesta" onClick={chat.stop} />
      ) : (
        <IconButton icon="send" variant="primary" label="Enviar (Intro)" type="submit" disabled={!input.trim()} />
      )}
    </form>
  )
}

export default function AssistantPage() {
  const params = useParams()
  const id = params.id ? Number(params.id) : undefined
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const chat = useChat(id, (created) => navigate(`/assistant/${created}`, { replace: true }))
  const open = (conversation?: number) => {
    chat.reset()
    navigate(conversation ? `/assistant/${conversation}` : '/assistant')
  }
  const conversations = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api<{ results: Conversation[] }>('/api/assistant/conversations/'),
  })
  const remove = useMutation({
    mutationFn: (conversation: number) => api(`/api/assistant/conversations/${conversation}/`, { method: 'DELETE' }),
    onSuccess: (_, conversation) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (conversation === id) open()
    },
  })

  // Una conversación borrada (o de otro usuario): se empieza una nueva
  const missing = chat.detail.error instanceof ApiError && chat.detail.error.status === 404
  useEffect(() => {
    if (missing) navigate('/assistant', { replace: true })
  }, [missing, navigate])

  const title = chat.detail.data?.title || 'Nueva conversación'

  if (chat.modelsLoading) return <Loading />
  if (chat.models.length === 0 && !conversations.data?.results.length) {
    return (
      <div className="nt-page">
        <EmptyState icon="chat" title="No hay modelos disponibles" adminPath="/admin/assistant/llmmodel/">
          {user?.is_staff
            ? 'Para usar Claude hay que definir ANTHROPIC_API_KEY; para modelos locales, levantar el perfil ollama y añadir el modelo al catálogo.'
            : 'Podrás usar el asistente cuando la administración configure un modelo.'}
        </EmptyState>
      </div>
    )
  }

  return (
    <div className="pt-assistant">
      <nav className="pt-assistant-history" aria-label="Conversaciones">
        <Button icon="plus" onClick={() => open()}>Nueva conversación</Button>
        <h2 className="nt-navgroup">Historial</h2>
        {conversations.data?.results.length === 0 && <p className="nt-muted t-caption">Todavía no hay conversaciones.</p>}
        {conversations.data?.results.map((c) => (
          <div className="pt-assistant-item" key={c.id}>
            <NavItem icon="chat" label={c.title || `Conversación ${c.id}`} href={`/assistant/${c.id}`} active={c.id === id} />
            <IconButton icon="trash" label={`Borrar «${c.title || `Conversación ${c.id}`}»`} onClick={() => { if (window.confirm('¿Borrar esta conversación?')) remove.mutate(c.id) }} />
          </div>
        ))}
      </nav>
      <section className="pt-assistant-main" aria-label={title}>
        <div className="pt-assistant-mobile">
          <select className="nt-field-control pt-assistant-select" aria-label="Conversación" value={id ?? ''} onChange={(e) => open(Number(e.target.value) || undefined)}>
            <option value="">Nueva conversación</option>
            {conversations.data?.results.map((c) => <option key={c.id} value={c.id}>{c.title || `Conversación ${c.id}`}</option>)}
          </select>
          {id !== undefined && <IconButton icon="trash" label="Borrar esta conversación" onClick={() => { if (window.confirm('¿Borrar esta conversación?')) remove.mutate(id) }} />}
        </div>
        <header className="pt-assistant-head">
          <h1 className="t-title-3 nt-ellipsis">{title}</h1>
          {chat.models.length > 0 ? (
            <select className="nt-field-control pt-assistant-select" aria-label="Modelo" value={chat.selectedModel ?? ''} disabled={chat.streaming} onChange={(e) => chat.setModelId(Number(e.target.value))}>
              {chat.models.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          ) : <span className="nt-muted t-caption">Sin modelos disponibles</span>}
        </header>
        <Messages chat={chat} />
        <Composer chat={chat} />
      </section>
    </div>
  )
}
