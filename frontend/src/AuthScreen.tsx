import { useState, type FormEvent } from 'react'
import AuthWorldMap from './components/AuthWorldMap.tsx'
import BrandMark from './BrandMark.tsx'
import { login, register } from './auth.ts'

type AuthMode = 'login' | 'register'

export default function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function showLogin() {
    setMode('login')
    setPassword('')
    setConfirmPassword('')
    setError(null)
    setSuccess(null)
  }

  function showRegister() {
    setMode('register')
    setPassword('')
    setConfirmPassword('')
    setError(null)
    setSuccess(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) {
      return
    }

    const trimmedEmail = email.trim()
    if (trimmedEmail === '') {
      setError('Email is required.')
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setError('Enter a valid email address.')
      return
    }
    if (password === '') {
      setError('Password is required.')
      return
    }
    if (mode === 'register') {
      if (password.length < 12) {
        setError('Password must be at least 12 characters.')
        return
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.')
        return
      }
    }

    setSubmitting(true)
    setError(null)

    try {
      if (mode === 'register') {
        await register(trimmedEmail, password)
        setEmail(trimmedEmail)
        setPassword('')
        setConfirmPassword('')
        setMode('login')
        setSuccess('Account created. Sign in to continue.')
      } else {
        await login(trimmedEmail, password)
      }
    } catch (err: unknown) {
      setSuccess(null)
      setError(
        err instanceof Error
          ? err.message
          : mode === 'register'
            ? 'Registration failed. Check the email and password.'
            : 'Login failed.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const isRegister = mode === 'register'

  return (
    <div className="auth-shell">
      <AuthWorldMap />
      <aside className="auth-hero">
        <div className="auth-hero-brand">
          <BrandMark size={40} />
          <div>
            <p className="brand-mark">Incident operations</p>
            <p className="brand-name">OpsPilot</p>
          </div>
        </div>
        <h1>A clear record of what broke, and why.</h1>
        <p className="subtitle">Intelligent Incident Operations</p>
        <ul className="auth-points">
          <li>Track incidents with severity, status, and the service involved.</li>
          <li>Read the log timeline attached to each incident.</li>
          <li>Ask Claude for a root-cause read and similar historical incidents.</li>
        </ul>
      </aside>

      <main className="auth-screen">
        <section className="auth-card" aria-labelledby="auth-heading">
          <h2 id="auth-heading">{isRegister ? 'Create account' : 'Sign in'}</h2>
          <p className="auth-intro">
            {isRegister
              ? 'Create a viewer account to sign in to OpsPilot.'
              : 'Sign in to view and manage incident operations.'}
          </p>

          {success && (
            <p className="auth-success" role="status">
              {success}
            </p>
          )}
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="form-field">
              <label className="form-label" htmlFor="auth-email">
                Email
              </label>
              <input
                id="auth-email"
                className="form-input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                disabled={submitting}
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="auth-password">
                Password
              </label>
              <input
                id="auth-password"
                className="form-input"
                type="password"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={isRegister ? 12 : undefined}
                disabled={submitting}
              />
              {isRegister && (
                <p className="form-hint">Use at least 12 characters.</p>
              )}
            </div>

            {isRegister && (
              <div className="form-field">
                <label className="form-label" htmlFor="auth-confirm-password">
                  Confirm password
                </label>
                <input
                  id="auth-confirm-password"
                  className="form-input"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                  disabled={submitting}
                />
              </div>
            )}

            <button
              type="submit"
              className="form-submit-button auth-submit"
              disabled={submitting}
              aria-busy={submitting}
            >
              {submitting
                ? isRegister
                  ? 'Creating account...'
                  : 'Signing in...'
                : isRegister
                  ? 'Create account'
                  : 'Sign in'}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  className="auth-switch-button"
                  onClick={showLogin}
                  disabled={submitting}
                >
                  Sign in
                </button>
              </>
            ) : (
              <>
                Need an account?{' '}
                <button
                  type="button"
                  className="auth-switch-button"
                  onClick={showRegister}
                  disabled={submitting}
                >
                  Create an account
                </button>
              </>
            )}
          </p>
        </section>
      </main>
    </div>
  )
}
