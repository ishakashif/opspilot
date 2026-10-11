import { useSyncExternalStore } from 'react'

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL
export const API_BASE_URL =
  configuredApiBaseUrl === undefined
    ? 'http://127.0.0.1:8000'
    : configuredApiBaseUrl.replace(/\/$/, '')

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RegisteredUser {
  id: number
  email: string
  role: string
  created_at: string
}

export interface AuthUser {
  id: number
  email: string
  role: string
  created_at: string
}

export interface AuthState {
  isAuthenticated: boolean
  user: AuthUser | null
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export class AuthenticationError extends ApiError {
  constructor(message: string) {
    super(401, message)
    this.name = 'AuthenticationError'
  }
}

export class PermissionError extends ApiError {
  constructor(message: string) {
    super(403, message)
    this.name = 'PermissionError'
  }
}

const signedOutState: AuthState = { isAuthenticated: false, user: null }

let accessToken: string | null = null
let authState: AuthState = signedOutState
const listeners = new Set<() => void>()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function getAuthState() {
  return authState
}

function publishAuthState(next: AuthState) {
  if (
    authState.isAuthenticated === next.isAuthenticated &&
    authState.user === next.user
  ) {
    return
  }
  authState = next
  for (const listener of listeners) {
    listener()
  }
}

function clearSession() {
  accessToken = null
  publishAuthState(signedOutState)
}

function setAccessToken(token: string | null) {
  accessToken = token
  if (token === null) {
    publishAuthState(signedOutState)
  }
}

export function useAuth(): AuthState {
  return useSyncExternalStore(subscribe, getAuthState, getAuthState)
}

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (response.status === 401) {
    throw new AuthenticationError(
      (await readErrorDetail(response)) ?? 'Invalid email or password.',
    )
  }

  if (!response.ok) {
    throw new ApiError(response.status, 'Login failed.')
  }

  const body: unknown = await response.json()
  if (!isTokenResponse(body)) {
    throw new ApiError(response.status, 'Login failed.')
  }

  accessToken = body.access_token
  try {
    const user = await loadCurrentUser()
    publishAuthState({ isAuthenticated: true, user })
  } catch (error) {
    clearSession()
    if (error instanceof AuthenticationError) {
      throw new ApiError(401, 'Could not load your account.')
    }
    throw error
  }
}

export async function register(
  email: string,
  password: string,
): Promise<RegisteredUser> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const detail = await readErrorDetail(response)
    throw new ApiError(
      response.status,
      detail ?? 'Registration failed. Check the email and password.',
    )
  }

  const body: unknown = await response.json()
  if (!isRegisteredUser(body)) {
    throw new ApiError(response.status, 'Registration failed.')
  }

  return body
}

export function logout() {
  clearSession()
}

async function loadCurrentUser(): Promise<AuthUser> {
  const response = await apiRequest('/auth/me')
  if (!response.ok) {
    throw new ApiError(response.status, 'Could not load your account.')
  }

  const body: unknown = await response.json()
  if (!isAuthUser(body)) {
    throw new ApiError(response.status, 'Could not load your account.')
  }

  return body
}

export async function apiRequest(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers)
  headers.delete('Authorization')
  if (accessToken !== null) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  if (response.status === 401) {
    setAccessToken(null)
    throw new AuthenticationError('Please log in again.')
  }

  if (response.status === 403) {
    throw new PermissionError(
      (await readErrorDetail(response)) ??
        'You do not have permission to perform this action.',
    )
  }

  return response
}

function isTokenResponse(value: unknown): value is TokenResponse {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const body = value as Record<string, unknown>
  return (
    typeof body.access_token === 'string' &&
    body.access_token.length > 0 &&
    typeof body.token_type === 'string'
  )
}

function isAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const body = value as Record<string, unknown>
  return (
    typeof body.id === 'number' &&
    typeof body.email === 'string' &&
    typeof body.role === 'string' &&
    typeof body.created_at === 'string'
  )
}

function isRegisteredUser(value: unknown): value is RegisteredUser {
  return isAuthUser(value)
}

async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json()
    if (typeof body !== 'object' || body === null || !('detail' in body)) {
      return null
    }
    const detail = body.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
  } catch {
    return null
  }
  return null
}
