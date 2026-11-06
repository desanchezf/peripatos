import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, type ReactNode } from 'react'
import { api, ApiError } from '../api/client'
import type { User } from '../api/types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

async function fetchMe(): Promise<User | null> {
  await api('/api/auth/csrf/') // deja la cookie csrftoken
  try {
    return await api<User>('/api/auth/me/')
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const { data: user = null, isPending } = useQuery({ queryKey: ['me'], queryFn: fetchMe, staleTime: Infinity })

  const login = async (username: string, password: string) => {
    const me = await api<User>('/api/auth/login/', { method: 'POST', json: { username, password } })
    // Django rota el token CSRF al iniciar sesión: se pide de nuevo
    await api('/api/auth/csrf/')
    queryClient.setQueryData(['me'], me)
  }

  const logout = async () => {
    await api('/api/auth/logout/', { method: 'POST' })
    // Primero «sin usuario» en la consulta que escucha la app: el armazón lleva a /login al momento.
    // clear() la quitaría de la caché y la app seguiría mostrando al usuario hasta recargar
    queryClient.setQueryData(['me'], null)
    // Después se descarta lo demás (lecturas, notas…) para que no lo vea quien entre luego
    queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'me' })
  }

  return <AuthContext value={{ user, loading: isPending, login, logout }}>{children}</AuthContext>
}

// oxlint-disable-next-line react/only-export-components
export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return context
}
