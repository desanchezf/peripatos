export interface Place {
  /** Página (PDF) o CFI (EPUB) */
  location: string
  label: string
  /** null mientras un EPUB aún calcula sus posiciones */
  percent: number | null
}

export interface TocItem {
  label: string
  location: string
  depth: number
}

export interface ViewerHandle {
  go: (location: string) => void
  next: () => void
  prev: () => void
  /** Texto seleccionado ahora mismo en el documento */
  selection: () => string
}

export interface ViewerProps {
  url: string
  initial: string
  onPlace: (place: Place) => void
  onToc: (items: TocItem[]) => void
  ref: React.Ref<ViewerHandle>
}
