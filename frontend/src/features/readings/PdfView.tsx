import type { PDFDocumentProxy } from 'pdfjs-dist'
import { useEffect, useImperativeHandle, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { IconButton } from '../../components'
import type { TocItem, ViewerProps } from './viewer'

// pdf.js usa APIs muy recientes: el worker legacy y este polyfill lo mantienen en navegadores de hace unos meses
pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/legacy/build/pdf.worker.min.mjs', import.meta.url).toString()
for (const type of [Map, WeakMap]) {
  const proto = type.prototype as unknown as Record<string, unknown>
  proto.getOrInsertComputed ??= function (this: Map<unknown, unknown>, key: unknown, compute: (key: unknown) => unknown) {
    if (!this.has(key)) this.set(key, compute(key))
    return this.get(key)
  }
}

interface OutlineNode {
  title: string
  dest: string | unknown[] | null
  items: OutlineNode[]
}

async function flattenOutline(pdf: PDFDocumentProxy, nodes: OutlineNode[], depth = 0): Promise<TocItem[]> {
  const items: TocItem[] = []
  for (const node of nodes) {
    try {
      const dest = typeof node.dest === 'string' ? await pdf.getDestination(node.dest) : node.dest
      if (dest) {
        const page = await pdf.getPageIndex(dest[0] as Parameters<PDFDocumentProxy['getPageIndex']>[0])
        items.push({ label: node.title, location: String(page + 1), depth })
      }
    } catch {
      // Una entrada del índice rota no debe dejar el documento sin índice
    }
    items.push(...(await flattenOutline(pdf, node.items ?? [], depth + 1)))
  }
  return items
}

export default function PdfView({ url, initial, onPlace, onToc, ref }: ViewerProps) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(() => Number(initial) || 1)
  const [zoom, setZoom] = useState(1)
  const [width, setWidth] = useState(0)
  const scroller = useRef<HTMLDivElement>(null)
  const total = pdf?.numPages ?? 1
  const current = Math.min(page, total)
  const go = (target: number) => setPage(Math.max(1, Math.min(target, total)))

  useImperativeHandle(ref, () => ({
    go: (location) => go(Number(location) || 1),
    next: () => go(current + 1),
    prev: () => go(current - 1),
    selection: () => window.getSelection()?.toString().trim() ?? '',
  }))

  useEffect(() => {
    const element = scroller.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!pdf) return
    onPlace({ location: String(current), label: `Página ${current}`, percent: (100 * current) / pdf.numPages })
    scroller.current?.scrollTo({ top: 0 })
    // oxlint-disable-next-line react/exhaustive-deps -- onPlace cambia en cada render de la página
  }, [current, pdf])

  return (
    <div className="pt-pdf">
      <div className="pt-pdf-bar">
        <label className="pt-pdf-page">
          <span className="nt-sr-only">Ir a la página</span>
          <input
            key={current}
            className="nt-field-control"
            type="number"
            min={1}
            max={total}
            defaultValue={current}
            onKeyDown={(e) => { if (e.key === 'Enter') go(Number(e.currentTarget.value) || current) }}
            onBlur={(e) => go(Number(e.currentTarget.value) || current)}
          />
          <span className="nt-muted">de {total}</span>
        </label>
        <IconButton icon="minus" label="Reducir" disabled={zoom <= 0.5} onClick={() => setZoom((z) => +(z - 0.1).toFixed(1))} />
        <span className="pt-pdf-zoom nt-muted">{Math.round(zoom * 100)} %</span>
        <IconButton icon="plus" label="Ampliar" disabled={zoom >= 3} onClick={() => setZoom((z) => +(z + 0.1).toFixed(1))} />
      </div>
      <div className="pt-pdf-scroll" ref={scroller}>
        <Document
          file={url}
          loading={<p className="pt-loading nt-muted">Abriendo el PDF…</p>}
          error={<p className="pt-loading nt-muted" role="alert">No se pudo abrir el PDF.</p>}
          onLoadSuccess={(document) => {
            setPdf(document)
            document.getOutline().then((outline) => flattenOutline(document, (outline ?? []) as OutlineNode[])).then(onToc).catch(() => onToc([]))
          }}
        >
          {width > 0 && <Page pageNumber={current} width={Math.min(width - 32, 960) * zoom} loading={null} />}
        </Document>
      </div>
    </div>
  )
}
