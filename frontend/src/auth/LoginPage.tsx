import { useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router'
import { Logo } from '../app/Logo'
import { Button, Card, TextField } from '../components'
import { errorText } from '../lib/format'
import { useAuth } from './AuthContext'

export default function LoginPage() {
  const { user, login } = useAuth()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  const from = (location.state as { from?: string } | null)?.from
  if (user) return <Navigate to={from && from !== '/login' ? from : '/'} replace />

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSending(true)
    setError('')
    try {
      await login(username, password)
    } catch (err) {
      setError(errorText(err) || 'No se pudo iniciar sesión')
    } finally {
      setSending(false)
    }
  }

  return (
    <main className="nt-login">
      <div className="nt-ws-brand nt-login-brand"><Logo size={36} />peripatos</div>
      <p className="nt-muted">Aprende mientras caminas. Aprende mientras trabajas.</p>
      <Card title="Iniciar sesión" icon="user">
        <form className="nt-form" onSubmit={submit}>
          <TextField label="Usuario" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
          <TextField label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required error={error || undefined} />
          <Button variant="primary" type="submit" className="nt-login-submit" disabled={sending}>{sending ? 'Entrando…' : 'Entrar'}</Button>
        </form>
      </Card>
    </main>
  )
}
