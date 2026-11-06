import type { ChatEvent } from './types'

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown) {
    super(errorMessage(data) ?? `Error ${status}`)
    this.status = status
    this.data = data
  }
}

/** Primer mensaje legible de una respuesta de error de DRF ({detail} o {campo: [errores]}) */
function errorMessage(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined
  const record = data as Record<string, unknown>
  if (typeof record.detail === 'string') return record.detail
  for (const value of Object.values(record)) {
    if (Array.isArray(value) && typeof value[0] === 'string') return value[0]
  }
  return undefined
}

function csrfToken(): string {
  return document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)?.[1] ?? ''
}

async function request(path: string, init: RequestInit & { json?: unknown } = {}): Promise<Response> {
  const { json, ...rest } = init
  const method = (rest.method ?? 'GET').toUpperCase()
  const headers = new Headers(rest.headers)
  // Con FormData (subidas) el navegador pone el Content-Type multipart con su boundary
  if (json !== undefined) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRFToken', csrfToken())

  const response = await fetch(path, {
    ...rest,
    headers,
    credentials: 'same-origin',
    body: json === undefined ? rest.body : JSON.stringify(json),
  })
  if (!response.ok) {
    const data = response.headers.get('Content-Type')?.includes('json') ? await response.json() : null
    throw new ApiError(response.status, data)
  }
  return response
}

export async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const response = await request(path, init)
  return (response.status === 204 ? undefined : await response.json()) as T
}

/** Envía un mensaje y entrega los eventos SSE según llegan (EventSource no admite POST) */
export async function* streamChat(conversationId: number, message: string, model: number, signal: AbortSignal): AsyncGenerator<ChatEvent> {
  const response = await request(`/api/assistant/conversations/${conversationId}/chat/`, { method: 'POST', json: { message, model }, signal })
  const reader = response.body!.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) return
    buffer += value
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''
    for (const event of events) {
      if (event.startsWith('data: ')) yield JSON.parse(event.slice(6)) as ChatEvent
    }
  }
}
