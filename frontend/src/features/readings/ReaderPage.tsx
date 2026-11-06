import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { lazy, Suspense, useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router'
import { api } from '../../api/client'
import type { Bookmark, Material, ReadingNote } from '../../api/types'
import { Badge, Button, Icon, IconButton, Loading, Markdown, TextField } from '../../components'
import { errorText } from '../../lib/format'
import { useStoredState } from '../../lib/storage'
import type { Place, TocItem, ViewerHandle } from './viewer'

const PdfView = lazy(() => import('./PdfView'))
const EpubView = lazy(() => import('./EpubView'))

type Tab = 'toc' | 'bookmarks' | 'notes'
const SAVE_DELAY = 800

export default function ReaderPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const key = ['material', id]
  const { data: material, isPending, error } = useQuery({
    queryKey: key,
    queryFn: () => api<Material>(`/api/theory/materials/${id}/`),
    // El visor no debe recolocarse porque la consulta se refresque mientras se lee
    staleTime: Infinity,
    gcTime: 0,
  })
  const { data: bookmarks = [] } = useQuery({ queryKey: ['bookmarks', id], queryFn: () => api<Bookmark[]>(`/api/theory/bookmarks/?material=${id}`) })
  const { data: notes = [] } = useQuery({ queryKey: ['notes', id], queryFn: () => api<ReadingNote[]>(`/api/theory/notes/?material=${id}`) })

  const viewer = useRef<ViewerHandle>(null)
  const [place, setPlace] = useState<Place | null>(null)
  const [percent, setPercent] = useState<number | null>(null)
  const [toc, setToc] = useState<TocItem[]>([])
  const [tab, setTab] = useState<Tab>('notes')
  const [panelOpen, setPanelOpen] = useStoredState('pt-reader-panel', window.innerWidth >= 768)
  const [draft, setDraft] = useState<{ id?: number; text: string; quote: string; location: string; label: string } | null>(null)
  const [noteError, setNoteError] = useState('')

  // --- Guardado del punto de lectura ---
  const pending = useRef<{ location: string; percent?: number } | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const flush = useCallback((keepalive = false) => {
    clearTimeout(timer.current)
    const body = pending.current
    if (!body) return
    pending.current = null
    // Si falla, se perdería solo este avance: el siguiente cambio de página vuelve a guardar
    api(`/api/theory/materials/${id}/progress/`, { method: 'PATCH', json: body, keepalive }).catch(() => {})
  }, [id])

  useEffect(() => {
    const onHide = () => flush(true)
    window.addEventListener('pagehide', onHide)
    return () => {
      window.removeEventListener('pagehide', onHide)
      flush(true)
    }
  }, [flush])

  const onPlace = useCallback((next: Place) => {
    setPlace(next)
    if (next.percent !== null) setPercent(next.percent)
    pending.current = { location: next.location, ...(next.percent !== null && { percent: Math.min(100, next.percent) }) }
    clearTimeout(timer.current)
    timer.current = setTimeout(flush, SAVE_DELAY)
  }, [flush])

  const setFinished = useMutation({
    mutationFn: (finished: boolean) => {
      flush()
      return api<Material>(`/api/theory/materials/${id}/progress/`, { method: 'PATCH', json: { finished } })
    },
    onSuccess: (updated) => queryClient.setQueryData(key, updated),
  })

  // --- Marcadores ---
  const refresh = (name: string) => queryClient.invalidateQueries({ queryKey: [name, id] })
  const here = place && bookmarks.find((bookmark) => bookmark.location === place.location)
  const toggleBookmark = useMutation({
    mutationFn: () => here
      ? api(`/api/theory/bookmarks/${here.id}/`, { method: 'DELETE' })
      : api('/api/theory/bookmarks/', { method: 'POST', json: { material: Number(id), location: place!.location, label: place!.label } }),
    onSuccess: () => refresh('bookmarks'),
  })
  const removeBookmark = useMutation({
    mutationFn: (bookmarkId: number) => api(`/api/theory/bookmarks/${bookmarkId}/`, { method: 'DELETE' }),
    onSuccess: () => refresh('bookmarks'),
  })

  // --- Notas ---
  const openNote = () => {
    setDraft({ text: '', quote: viewer.current?.selection() ?? '', location: place?.location ?? '', label: place?.label ?? '' })
    setNoteError('')
    setTab('notes')
    setPanelOpen(true)
  }
  const saveNote = useMutation({
    mutationFn: ({ id: noteId, ...fields }: NonNullable<typeof draft>) => noteId
      ? api(`/api/theory/notes/${noteId}/`, { method: 'PATCH', json: { text: fields.text } })
      : api('/api/theory/notes/', { method: 'POST', json: { material: Number(id), ...fields } }),
    onSuccess: () => { setDraft(null); refresh('notes') },
    onError: (err) => setNoteError(errorText(err) || 'No se pudo guardar la nota'),
  })
  const removeNote = useMutation({
    mutationFn: (noteId: number) => api(`/api/theory/notes/${noteId}/`, { method: 'DELETE' }),
    onSuccess: () => refresh('notes'),
  })
  const submitNote = (event: FormEvent) => {
    event.preventDefault()
    if (draft?.text.trim()) saveNote.mutate(draft)
  }

  // --- Teclado: flechas para pasar de página fuera de los campos de texto ---
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      if (target.closest('input, textarea, select, [contenteditable]')) return
      if (event.key === 'ArrowRight') viewer.current?.next()
      if (event.key === 'ArrowLeft') viewer.current?.prev()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (error) throw error
  if (isPending) return <Loading />

  const hasViewer = material.file_url !== null
  const finished = material.progress.finished
  const shown = percent ?? material.progress.percent
  const tabs: { id: Tab; label: string; count?: number }[] = [
    ...(hasViewer ? [{ id: 'toc' as const, label: 'Índice' }, { id: 'bookmarks' as const, label: 'Marcadores', count: bookmarks.length }] : []),
    { id: 'notes', label: 'Notas', count: notes.length },
  ]
  const Viewer = material.format === 'epub' ? EpubView : PdfView

  return (
    <div className={['pt-reader', panelOpen && 'pt-reader-panelopen'].filter(Boolean).join(' ')}>
      <header className="pt-reader-bar">
        <Link className="nt-iconbtn" to="/readings" aria-label="Volver a lecturas" title="Volver a lecturas"><Icon name="chevron-left" size={16} /></Link>
        <h1 className="pt-reader-title nt-ellipsis" title={material.title}>{material.title}</h1>
        {hasViewer && (
          <>
            <IconButton icon="chevron-left" label="Página anterior (←)" onClick={() => viewer.current?.prev()} />
            <span className="pt-reader-place nt-ellipsis nt-muted" aria-live="polite">{place?.label ?? ''}</span>
            <IconButton icon="chevron-right" label="Página siguiente (→)" onClick={() => viewer.current?.next()} />
            <span className="pt-reader-percent nt-muted">{Math.round(shown)} %</span>
            <IconButton
              icon="bookmark"
              label={here ? 'Quitar marcador' : 'Marcar esta página'}
              aria-pressed={Boolean(here)}
              className={here ? 'pt-iconbtn-on' : undefined}
              disabled={!place || toggleBookmark.isPending}
              onClick={() => toggleBookmark.mutate()}
            />
          </>
        )}
        {/* mouseDown: pulsar el botón no debe perder el texto seleccionado */}
        <IconButton icon="note" label="Añadir una nota (usa el texto seleccionado)" onMouseDown={(e) => e.preventDefault()} onClick={openNote} />
        <Button size="sm" icon={finished ? undefined : 'check'} disabled={setFinished.isPending} onClick={() => setFinished.mutate(!finished)}>
          {finished ? 'Marcar pendiente' : 'Marcar terminada'}
        </Button>
        <IconButton icon="panel" label={panelOpen ? 'Ocultar el panel' : 'Mostrar el panel'} aria-expanded={panelOpen} onClick={() => setPanelOpen(!panelOpen)} />
      </header>

      <div className="pt-reader-body">
        <div className="pt-reader-doc">
          {hasViewer ? (
            <Suspense fallback={<Loading />}>
              <Viewer url={material.file_url!} initial={material.progress.location} onPlace={onPlace} onToc={setToc} ref={viewer} />
            </Suspense>
          ) : (
            <article className="pt-reader-text">
              {material.content ? <Markdown>{material.content}</Markdown> : <p className="nt-muted">Este material no tiene contenido propio.</p>}
              {material.source_url && <p><a href={material.source_url} target="_blank" rel="noopener noreferrer">Abrir el enlace <Icon name="external" size={14} /></a></p>}
            </article>
          )}
        </div>

        {panelOpen && (
          <aside className="pt-reader-panel" aria-label="Índice, marcadores y notas">
            <div className="nt-segmented" role="group" aria-label="Sección del panel">
              {tabs.map((item) => (
                <button key={item.id} type="button" aria-pressed={tab === item.id || tabs.length === 1} onClick={() => setTab(item.id)}>
                  {item.label}{item.count ? ` (${item.count})` : ''}
                </button>
              ))}
            </div>

            {tab === 'toc' && hasViewer && (
              toc.length === 0
                ? <p className="pt-list-empty nt-muted">Este documento no tiene índice.</p>
                : <ul className="pt-toc">
                    {toc.map((item, index) => (
                      <li key={`${item.location}-${index}`} style={{ paddingLeft: item.depth * 12 }}>
                        <button type="button" onClick={() => viewer.current?.go(item.location)}>{item.label}</button>
                      </li>
                    ))}
                  </ul>
            )}

            {tab === 'bookmarks' && hasViewer && (
              bookmarks.length === 0
                ? <p className="pt-list-empty nt-muted">Aún no has marcado ninguna página.</p>
                : <ul className="pt-toc">
                    {bookmarks.map((bookmark) => (
                      <li key={bookmark.id} className="pt-toc-row">
                        <button type="button" className="nt-grow" onClick={() => viewer.current?.go(bookmark.location)}>{bookmark.label || 'Marcador'}</button>
                        <IconButton icon="trash" label="Quitar marcador" onClick={() => removeBookmark.mutate(bookmark.id)} />
                      </li>
                    ))}
                  </ul>
            )}

            {(tab === 'notes' || !hasViewer) && (
              <div className="pt-notes">
                {draft ? (
                  <form className="nt-form" onSubmit={submitNote}>
                    {draft.quote && <blockquote className="pt-quote">{draft.quote}</blockquote>}
                    <TextField
                      label={draft.label ? `Nota · ${draft.label}` : 'Nota'}
                      multiline rows={5} autoFocus required
                      value={draft.text}
                      onChange={(e) => setDraft({ ...draft, text: e.target.value })}
                      error={noteError || undefined}
                    />
                    <div className="nt-form-actions">
                      <Button size="sm" variant="ghost" onClick={() => setDraft(null)}>Cancelar</Button>
                      <Button size="sm" variant="primary" type="submit" disabled={saveNote.isPending}>Guardar</Button>
                    </div>
                  </form>
                ) : (
                  <Button size="sm" icon="plus" onMouseDown={(e) => e.preventDefault()} onClick={openNote}>Nueva nota</Button>
                )}
                {notes.length === 0 && !draft && <p className="pt-list-empty nt-muted">Selecciona texto y añade una nota para citarlo.</p>}
                <ul className="pt-note-list">
                  {notes.map((note) => (
                    <li key={note.id} className="pt-note">
                      {note.quote && <blockquote className="pt-quote">{note.quote}</blockquote>}
                      <p className="pt-note-text">{note.text}</p>
                      <div className="pt-note-foot">
                        {note.location && hasViewer
                          ? <button type="button" className="pt-note-go" onClick={() => viewer.current?.go(note.location)}>{note.label || 'Ir a la nota'}</button>
                          : <span />}
                        <span className="nt-grow" />
                        <IconButton icon="edit" label="Editar nota" onClick={() => setDraft({ id: note.id, text: note.text, quote: note.quote, location: note.location, label: note.label })} />
                        <IconButton icon="trash" label="Borrar nota" onClick={() => { if (window.confirm('¿Borrar esta nota?')) removeNote.mutate(note.id) }} />
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {finished && <Badge tone="success" icon="check">Lectura terminada</Badge>}
          </aside>
        )}
      </div>
    </div>
  )
}
