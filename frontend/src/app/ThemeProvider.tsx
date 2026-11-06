import { createContext, useContext, useState, type ReactNode } from 'react'

export type Palette = 'lava' | 'citrus' | 'bloom'
export type Mode = 'light' | 'dark'
export type ThemeId = `${Palette}-${Mode}`

const KEY = 'nt-theme'
const THEMES: ThemeId[] = ['lava-light', 'lava-dark', 'citrus-light', 'citrus-dark', 'bloom-light', 'bloom-dark']

interface ThemeState {
  theme: ThemeId
  palette: Palette
  mode: Mode
  setTheme(t: ThemeId): void
  setPalette(p: Palette): void
  setMode(m: Mode): void
}

const Ctx = createContext<ThemeState | null>(null)

function initial(): ThemeId {
  try {
    const t = localStorage.getItem(KEY) as ThemeId | null
    if (t && THEMES.includes(t)) return t
  } catch { /* sin localStorage: tema del sistema */ }
  const dark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  return dark ? 'lava-dark' : 'lava-light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>(() => {
    const t = initial()
    document.documentElement.dataset.theme = t
    return t
  })

  // El atributo se cambia antes de volver a pintar: gráficos, Mermaid y CodeMirror leen ya los tokens nuevos
  const setTheme = (t: ThemeId) => {
    document.documentElement.dataset.theme = t
    try { localStorage.setItem(KEY, t) } catch { /* se pierde al recargar */ }
    setThemeState(t)
  }

  const [palette, mode] = theme.split('-') as [Palette, Mode]
  return (
    <Ctx value={{ theme, palette, mode, setTheme, setPalette: (p) => setTheme(`${p}-${mode}`), setMode: (m) => setTheme(`${palette}-${m}`) }}>
      {children}
    </Ctx>
  )
}

// oxlint-disable-next-line react/only-export-components
export const useTheme = () => {
  const c = useContext(Ctx)
  if (!c) throw new Error('useTheme fuera de ThemeProvider')
  return c
}
