import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { api, ApiError, streamChat } from '../../api/client'
import type { Conversation, ConversationDetail, LLMModel } from '../../api/types'

export interface PendingTurn {
  /** Mensajes guardados antes de este turno. El backend guarda el turno mientras se muestra: lo posterior se oculta hasta acabar */
  base: number
  user: string
  content: string
  error: string
}

const errorText = (err: unknown) => (err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor.')

/** `onCreated` recibe el id de la conversación que se crea al enviar el primer mensaje */
export function useChat(conversationId: number | undefined, onCreated: (id: number) => void) {
  const queryClient = useQueryClient()
  const models = useQuery({ queryKey: ['llm-models'], queryFn: () => api<LLMModel[]>('/api/assistant/models/') })
  const detail = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => api<ConversationDetail>(`/api/assistant/conversations/${conversationId}/`),
    enabled: conversationId !== undefined,
  })

  const [modelId, setModelId] = useState<number>()
  const [pending, setPending] = useState<PendingTurn | null>(null)
  const [streaming, setStreaming] = useState(false)
  const abort = useRef<AbortController | null>(null)
  const turnConversation = useRef(conversationId)

  // Salir de la página corta la respuesta: el backend guarda lo recibido hasta ese momento
  useEffect(() => () => abort.current?.abort(), [])

  // Cambiar de conversación, también con el botón Atrás, abandona el turno en curso
  useEffect(() => {
    if (conversationId === turnConversation.current) return
    turnConversation.current = conversationId
    abort.current?.abort()
    setPending(null)
  }, [conversationId])

  const available = models.data ?? []
  const usable = (id: number | null | undefined) => (id && available.some((m) => m.id === id) ? id : undefined)
  // El elegido, el de la conversación o el primero del catálogo
  const selectedModel = usable(modelId) ?? usable(detail.data?.model) ?? available[0]?.id

  const saved = conversationId !== undefined ? detail.data?.messages ?? [] : []

  const refresh = (id: number) =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ['conversation', id] }),
      queryClient.invalidateQueries({ queryKey: ['conversations'] }),
    ])

  const send = async (text: string) => {
    if (streaming || !selectedModel) return false
    const controller = new AbortController()
    abort.current = controller
    const turn: PendingTurn = { base: saved.length, user: text, content: '', error: '' }
    setPending({ ...turn })
    setStreaming(true)

    let id = conversationId
    let finished = false
    try {
      if (id === undefined) {
        const created = await api<Conversation>('/api/assistant/conversations/', { method: 'POST', json: { model: selectedModel } })
        id = created.id
        turnConversation.current = id
        onCreated(id)
      }
      for await (const event of streamChat(id, text, selectedModel, controller.signal)) {
        if (event.type === 'text') turn.content += event.text
        else if (event.type === 'error') turn.error = event.message
        else finished = true
        setPending({ ...turn })
      }
      if (!finished && !turn.error) turn.error = 'La respuesta se interrumpió.'
    } catch (err) {
      if (!controller.signal.aborted) turn.error = errorText(err)
    }

    setStreaming(false)
    if (id !== undefined) {
      // Al parar, el backend guarda lo recibido cuando nota el corte: se le da margen antes de recargar
      if (controller.signal.aborted) await new Promise((resolve) => setTimeout(resolve, 1500))
      await refresh(id)
    }
    // Mientras tanto puede haber empezado otro turno
    if (abort.current === controller) setPending(turn.error ? { ...turn } : null)
    return true
  }

  const stop = () => abort.current?.abort()

  return {
    models: available,
    modelsLoading: models.isPending,
    modelLabel: (id: number | null) => available.find((m) => m.id === id)?.label,
    selectedModel,
    setModelId,
    detail,
    messages: pending ? saved.slice(0, pending.base) : saved,
    pending,
    streaming,
    send,
    stop,
    /** Corta la respuesta en curso y olvida el turno pendiente */
    reset: () => {
      stop()
      setPending(null)
    },
  }
}
