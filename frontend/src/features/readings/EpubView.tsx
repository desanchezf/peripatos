import ePub, { type Book, type Rendition } from 'epubjs'
import { useEffect, useImperativeHandle, useRef, useState } from 'react'
import { useTheme } from '../../app/ThemeProvider'
import { cssVar } from '../../lib/storage'
import type { Place, TocItem, ViewerProps } from './viewer'

interface NavItem {
  label: string
  href: string
  subitems?: NavItem[]
}

const flatten = (items: NavItem[], depth = 0): TocItem[] =>
  items.flatMap((item) => [{ label: item.label.trim(), location: item.href, depth }, ...flatten(item.subitems ?? [], depth + 1)])

export default function EpubView({ url, initial, onPlace, onToc, ref }: ViewerProps) {
  const host = useRef<HTMLDivElement>(null)
  const rendition = useRef<Rendition | null>(null)
  const selected = useRef('')
  const callbacks = useRef({ onPlace, onToc, initial })
  const [failed, setFailed] = useState(false)
  const { mode } = useTheme()

  useEffect(() => {
    callbacks.current = { onPlace, onToc, initial: callbacks.current.initial }
  })

  useImperativeHandle(ref, () => ({
    go: (location) => void rendition.current?.display(location),
    next: () => void rendition.current?.next(),
    prev: () => void rendition.current?.prev(),
    selection: () => selected.current,
  }))

  useEffect(() => {
    const state: { cancelled: boolean; book?: Book } = { cancelled: false }
    const element = host.current!
    const observer = new ResizeObserver(() => rendition.current?.resize(element.clientWidth, element.clientHeight))

    const open = async () => {
      const response = await fetch(url, { credentials: 'same-origin' })
      if (!response.ok) throw new Error(`Error ${response.status}`)
      const data = await response.arrayBuffer()
      if (state.cancelled) return

      const book = ePub(data)
      state.book = book
      const view = book.renderTo(element, { width: '100%', height: '100%', flow: 'paginated', spread: 'none' })
      rendition.current = view
      const applyTheme = () => {
        view.themes.override('color', cssVar('--ink'))
        view.themes.override('background', 'transparent')
      }
      applyTheme()
      view.on('selected', (_cfi: string, contents: { window: Window }) => {
        selected.current = contents.window.getSelection()?.toString().trim() ?? ''
      })
      view.on('keyup', (event: KeyboardEvent) => {
        if (event.key === 'ArrowRight') void view.next()
        if (event.key === 'ArrowLeft') void view.prev()
      })

      const report = (start: { cfi: string; href: string }) => {
        const chapter = book.navigation?.get(start.href)
        const ready = book.locations.length() > 0
        const place: Place = {
          location: start.cfi,
          label: chapter?.label?.trim() || 'Posición guardada',
          percent: ready ? book.locations.percentageFromCfi(start.cfi) * 100 : null,
        }
        callbacks.current.onPlace(place)
      }
      view.on('relocated', (location: { start: { cfi: string; href: string } }) => {
        selected.current = ''
        report(location.start)
      })

      await book.ready
      if (state.cancelled) return
      callbacks.current.onToc(flatten((book.navigation?.toc ?? []) as unknown as NavItem[]))
      // Si el CFI guardado ya no es válido, se abre por el principio
      await view.display(callbacks.current.initial || undefined).catch(() => view.display())
      observer.observe(element)
      // Las posiciones (para el %) se calculan al abrir: en libros grandes tarda unos segundos
      await book.locations.generate(1024)
      const current = view.currentLocation() as unknown as { start?: { cfi: string; href: string } }
      if (!state.cancelled && current?.start) report(current.start)
    }

    open().catch(() => { if (!state.cancelled) setFailed(true) })
    return () => {
      state.cancelled = true
      observer.disconnect()
      rendition.current = null
      state.book?.destroy()
      element.replaceChildren()
    }
  }, [url])

  useEffect(() => {
    rendition.current?.themes.override('color', cssVar('--ink'))
  }, [mode])

  if (failed) return <p className="pt-loading nt-muted" role="alert">No se pudo abrir el EPUB.</p>
  return <div className="pt-epub" ref={host} />
}
