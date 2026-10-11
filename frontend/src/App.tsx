import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import './App.css'
import AuthScreen from './AuthScreen.tsx'
import BrandMark from './BrandMark.tsx'
import { apiRequest, logout, useAuth, type AuthUser } from './auth.ts'

interface Incident {
  id: number
  title: string
  description: string
  severity: string
  status: string
  service: string
  created_at: string
  updated_at: string
}

interface Log {
  id: number
  incident_id: number 
  level: string
  message: string
  source: string
  timestamp: string
}

interface IncidentAnalysis {
  root_cause: string
  evidence: string[]
  recommended_actions: string[]
  confidence: string
}

interface SimilarIncident {
  incident_id: number
  title: string
  service: string
  severity: string
  status: string
  similarity: string
  reason: string
  relevant_pattern: string
}

interface SimilarIncidentsResponse {
  incidents: SimilarIncident[]
}

interface LogDraft {
  key: number
  level: string
  source: string
  message: string
}

function createLogDraft(key: number): LogDraft {
  return {
    key,
    level: 'INFO',
    source: '',
    message: '',
  }
}

function sortLogs(entries: Log[]) {
  return [...entries].sort((a, b) => {
    const timeDiff =
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    if (timeDiff !== 0) {
      return timeDiff
    }
    return a.id - b.id
  })
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString()
}

function confidenceTone(confidence: string) {
  const token = confidence.trim().toLowerCase().split(/\s+/)[0] ?? ''
  if (token === 'high' || token === 'medium' || token === 'low') {
    return token
  }
  return 'unknown'
}

function similarityTone(similarity: string) {
  const token = similarity.trim().toLowerCase().split(/\s+/)[0] ?? ''
  if (token === 'high' || token === 'medium' || token === 'low') {
    return token
  }
  return 'unknown'
}

function AppShell({
  user,
  isEngineer,
  viewingIncident,
  onShowIncidents,
  onLogout,
  onNewIncident,
  children,
}: {
  user: AuthUser
  isEngineer: boolean
  viewingIncident: boolean
  onShowIncidents: () => void
  onLogout: () => void
  onNewIncident: () => void
  children: ReactNode
}) {
  const userInitial = user.email.trim().charAt(0).toUpperCase() || 'O'

  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace-main">
        Skip to content
      </a>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <BrandMark />
          <div className="sidebar-brand-copy">
            <p className="brand-name">OpsPilot</p>
            <p className="brand-mark">Incident operations</p>
          </div>
        </div>
        <nav className="sidebar-nav" aria-label="Primary">
          <button
            type="button"
            className={`nav-item${viewingIncident ? '' : ' is-active'}`}
            aria-current={viewingIncident ? undefined : 'page'}
            onClick={() => {
              if (viewingIncident) {
                onShowIncidents()
              }
            }}
          >
            <span className="nav-glyph" aria-hidden="true" />
            Incidents
          </button>
        </nav>
        <p className="sidebar-note">Intelligent Incident Operations</p>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-title">
            <p className="eyebrow">OpsPilot</p>
            <p className="topbar-context">
              {viewingIncident ? 'Incident detail' : 'Incidents'}
            </p>
          </div>
          <div className="header-actions">
            <p className="signed-in">
              <span className="user-avatar" aria-hidden="true">
                {userInitial}
              </span>
              <span className="signed-in-copy">
                <span className="signed-in-email">{user.email}</span>
                <span className="signed-in-role">{user.role}</span>
              </span>
            </p>
            <button type="button" className="logout-button" onClick={onLogout}>
              Log out
            </button>
            {isEngineer && !viewingIncident && (
              <button
                type="button"
                className="new-incident-button"
                onClick={onNewIncident}
              >
                New Incident
              </button>
            )}
          </div>
        </header>
        <main id="workspace-main" className="workspace-main">
          {children}
        </main>
      </div>
    </div>
  )
}

function Dashboard({
  user,
  onLogout,
}: {
  user: AuthUser
  onLogout: () => void
}) {
  const isEngineer = user.role === 'engineer'
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [logs, setLogs] = useState<Log[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsError, setLogsError] = useState<string | null>(null)
  const [createFormOpen, setCreateFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [service, setService] = useState('')
  const [severity, setSeverity] = useState('medium')
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [addLogsOpen, setAddLogsOpen] = useState(false)
  const [logDrafts, setLogDrafts] = useState<LogDraft[]>(() => [createLogDraft(1)])
  const [nextLogKey, setNextLogKey] = useState(2)
  const [addLogsLoading, setAddLogsLoading] = useState(false)
  const [addLogsError, setAddLogsError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<IncidentAnalysis | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const analysisRequestId = useRef<number | null>(null)
  const [similarIncidents, setSimilarIncidents] = useState<SimilarIncident[]>([])
  const [similarIncidentsLoading, setSimilarIncidentsLoading] = useState(false)
  const [similarIncidentsError, setSimilarIncidentsError] = useState<string | null>(null)
  const [similarIncidentsLoaded, setSimilarIncidentsLoaded] = useState(false)
  const similarIncidentsRequestId = useRef<number | null>(null)

  useEffect(() => {
    apiRequest('/incidents/')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to fetch incidents')
        }
        return response.json()
      })
      .then((data: Incident[]) => {
        setIncidents(data)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch incidents')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  function resetAnalysis() {
    analysisRequestId.current = null
    setAnalysis(null)
    setAnalysisLoading(false)
    setAnalysisError(null)
  }

  function resetSimilarIncidents() {
    similarIncidentsRequestId.current = null
    setSimilarIncidents([])
    setSimilarIncidentsLoading(false)
    setSimilarIncidentsError(null)
    setSimilarIncidentsLoaded(false)
  }

  function resetAddLogsForm() {
    setAddLogsOpen(false)
    setLogDrafts([createLogDraft(1)])
    setNextLogKey(2)
    setAddLogsError(null)
  }

  function updateLogDraft(
    key: number,
    field: 'level' | 'source' | 'message',
    value: string,
  ) {
    setLogDrafts((current) =>
      current.map((draft) =>
        draft.key === key ? { ...draft, [field]: value } : draft,
      ),
    )
  }

  function addLogDraft() {
    setLogDrafts((current) => [...current, createLogDraft(nextLogKey)])
    setNextLogKey((current) => current + 1)
  }

  function removeLogDraft(key: number) {
    setLogDrafts((current) =>
      current.length <= 1 ? current : current.filter((draft) => draft.key !== key),
    )
  }

  async function handleSelectIncident(incident: Incident) {
    setSelectedIncident(incident)
    setStatusError(null)
    resetAddLogsForm()
    resetAnalysis()
    resetSimilarIncidents()
    setLogs([])
    setLogsLoading(true)
    setLogsError(null)

    try {
      const response = await apiRequest(
        `/incidents/${incident.id}/logs/`,
      )

      if (!response.ok) {
        throw new Error('Failed to fetch incident logs')
      }

      const data: Log[] = await response.json()
      setLogs(data)
    } catch (err: unknown) {
      setLogsError(
        err instanceof Error ? err.message : 'Failed to fetch incident logs'
      )
    } finally {
      setLogsLoading(false)
    }
  }

  function resetCreateForm() {
    setCreateFormOpen(false)
    setTitle('')
    setDescription('')
    setService('')
    setSeverity('medium')
    setCreateError(null)
  }

  async function handleCreateIncident(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isEngineer || createLoading) {
      return
    }

    setCreateLoading(true)
    setCreateError(null)

    try {
      const response = await apiRequest('/incidents/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          description,
          severity,
          service,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create incident')
      }

      const created: Incident = await response.json()
      setIncidents((current) => [...current, created])
      resetCreateForm()
    } catch (err: unknown) {
      setCreateError(
        err instanceof Error ? err.message : 'Failed to create incident',
      )
    } finally {
      setCreateLoading(false)
    }
  }

  async function handleStatusChange(newStatus: string) {
    if (
      !isEngineer ||
      !selectedIncident ||
      statusUpdating ||
      newStatus === selectedIncident.status
    ) {
      return
    }

    const incidentId = selectedIncident.id
    setStatusUpdating(true)
    setStatusError(null)

    try {
      const response = await apiRequest(
        `/incidents/${incidentId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status: newStatus }),
        },
      )

      if (!response.ok) {
        throw new Error('Failed to update incident status')
      }

      const updated: Incident = await response.json()
      setSelectedIncident((current) =>
        current?.id === updated.id ? updated : current,
      )
      setIncidents((current) =>
        current.map((incident) =>
          incident.id === updated.id ? updated : incident,
        ),
      )
    } catch (err: unknown) {
      setStatusError(
        err instanceof Error ? err.message : 'Failed to update incident status',
      )
    } finally {
      setStatusUpdating(false)
    }
  }

  async function handleAddLogs(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isEngineer || !selectedIncident || addLogsLoading) {
      return
    }

    const missingField = logDrafts.some(
      (draft) => draft.source.trim() === '' || draft.message.trim() === '',
    )
    if (missingField) {
      setAddLogsError('Source and message are required for every log.')
      return
    }

    const incidentId = selectedIncident.id
    setAddLogsLoading(true)
    setAddLogsError(null)

    try {
      const response = await apiRequest(
        `/incidents/${incidentId}/logs/bulk`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            logs: logDrafts.map((draft) => ({
              level: draft.level,
              message: draft.message.trim(),
              source: draft.source.trim(),
            })),
          }),
        },
      )

      if (!response.ok) {
        throw new Error('Failed to add logs')
      }

      const created: Log[] = await response.json()
      setLogs((current) => sortLogs([...current, ...created]))
      setLogsError(null)
      resetAddLogsForm()
    } catch (err: unknown) {
      setAddLogsError(err instanceof Error ? err.message : 'Failed to add logs')
    } finally {
      setAddLogsLoading(false)
    }
  }

  async function handleAnalyzeIncident() {
    if (!isEngineer || !selectedIncident || analysisLoading) {
      return
    }

    const incidentId = selectedIncident.id
    analysisRequestId.current = incidentId
    setAnalysisError(null)
    setAnalysisLoading(true)

    try {
      const response = await apiRequest(
        `/incidents/${incidentId}/analyze`,
        { method: 'POST' },
      )

      if (!response.ok) {
        throw new Error('Incident analysis failed. Try again.')
      }

      const data: IncidentAnalysis = await response.json()
      if (analysisRequestId.current !== incidentId) {
        return
      }
      setAnalysis(data)
    } catch (err: unknown) {
      if (analysisRequestId.current !== incidentId) {
        return
      }
      setAnalysisError(
        err instanceof Error
          ? err.message
          : 'Incident analysis failed. Try again.',
      )
    } finally {
      if (analysisRequestId.current === incidentId) {
        setAnalysisLoading(false)
      }
    }
  }

  async function handleFindSimilarIncidents() {
    if (!isEngineer || !selectedIncident || similarIncidentsLoading) {
      return
    }

    const incidentId = selectedIncident.id
    similarIncidentsRequestId.current = incidentId
    setSimilarIncidentsError(null)
    setSimilarIncidentsLoading(true)

    try {
      const response = await apiRequest(
        `/incidents/${incidentId}/similar`,
      )

      if (!response.ok) {
        throw new Error('Similar incidents could not be loaded. Try again.')
      }

      const data: SimilarIncidentsResponse = await response.json()
      if (!Array.isArray(data.incidents)) {
        throw new Error('Similar incidents could not be loaded. Try again.')
      }
      if (similarIncidentsRequestId.current !== incidentId) {
        return
      }
      setSimilarIncidents(data.incidents)
      setSimilarIncidentsLoaded(true)
    } catch (err: unknown) {
      if (similarIncidentsRequestId.current !== incidentId) {
        return
      }
      setSimilarIncidentsError(
        err instanceof Error
          ? err.message
          : 'Similar incidents could not be loaded. Try again.',
      )
    } finally {
      if (similarIncidentsRequestId.current === incidentId) {
        setSimilarIncidentsLoading(false)
      }
    }
  }

  const totalIncidents = incidents.length
  const activeIncidents = incidents.filter(
    (incident) => incident.status !== 'resolved',
  ).length
  const criticalIncidents = incidents.filter(
    (incident) => incident.severity === 'critical',
  ).length
  const investigatingIncidents = incidents.filter(
    (incident) => incident.status === 'investigating',
  ).length
  function leaveIncident() {
    setSelectedIncident(null)
    setLogs([])
    setLogsError(null)
    setStatusError(null)
    resetAddLogsForm()
    resetAnalysis()
    resetSimilarIncidents()
  }

  if (selectedIncident) {
    return (
      <AppShell
        user={user}
        isEngineer={isEngineer}
        viewingIncident
        onShowIncidents={leaveIncident}
        onLogout={onLogout}
        onNewIncident={() => setCreateFormOpen(true)}
      >
        <article className="incident-detail">
          <header className="detail-header">
            <div className="detail-toolbar">
              <button
                type="button"
                className="back-button"
                onClick={leaveIncident}
              >
                ← Back to incidents
              </button>
            </div>
            <h1>{selectedIncident.title}</h1>
            <div className="detail-badges">
              <span
                className={`severity-badge severity-${selectedIncident.severity}`}
              >
                {selectedIncident.severity}
              </span>
              <span
                className={`status-badge status-${selectedIncident.status}`}
              >
                {selectedIncident.status}
              </span>
            </div>
          </header>

          {isEngineer && (
          <div className="status-control">
            <label className="status-control-label" htmlFor="incident-status">
              Update status
            </label>
            <select
              id="incident-status"
              className="status-select"
              value={selectedIncident.status}
              onChange={(event) => handleStatusChange(event.target.value)}
              disabled={statusUpdating}
              aria-busy={statusUpdating}
            >
              <option value="open">open</option>
              <option value="investigating">investigating</option>
              <option value="resolved">resolved</option>
            </select>
            {statusUpdating && (
              <span className="status-updating" aria-live="polite">
                Updating...
              </span>
            )}
            {statusError && (
              <p className="status-error" role="alert">
                {statusError}
              </p>
            )}
          </div>
          )}

          <dl className="incident-metadata">
            <div>
              <dt>Service</dt>
              <dd className="meta-service">{selectedIncident.service}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>
                <time dateTime={selectedIncident.created_at}>
                  {formatTimestamp(selectedIncident.created_at)}
                </time>
              </dd>
            </div>
            <div>
              <dt>Updated</dt>
              <dd>
                <time dateTime={selectedIncident.updated_at}>
                  {formatTimestamp(selectedIncident.updated_at)}
                </time>
              </dd>
            </div>
          </dl>

          <section className="description-panel">
            <p>{selectedIncident.description}</p>
          </section>

          {isEngineer && (
          <section
            className="analysis-panel"
            aria-labelledby="incident-analysis-heading"
          >
            <div className="analysis-panel-header">
              <div>
                <h2 id="incident-analysis-heading">AI Incident Analysis</h2>
                {!analysis && (
                  <p className="analysis-intro">
                    OpsPilot analyzes the incident details and logs to identify
                    likely causes and recommended actions.
                  </p>
                )}
              </div>
              {analysis && (
                <button
                  type="button"
                  className="analyze-button"
                  onClick={handleAnalyzeIncident}
                  disabled={analysisLoading}
                  aria-busy={analysisLoading}
                >
                  {analysisLoading ? 'Analyzing...' : 'Re-analyze'}
                </button>
              )}
            </div>

            {analysisError && (
              <p className="analysis-error" role="alert">
                {analysisError}
              </p>
            )}

            {analysisLoading && (
              <div className="analysis-loading-block" aria-live="polite">
                <p className="analysis-loading">
                  Analyzing incident details and logs...
                </p>
                <div className="skeleton-analysis" aria-hidden="true">
                  <span className="skeleton" />
                  <span className="skeleton" />
                  <span className="skeleton" />
                </div>
              </div>
            )}

            {!analysis && (
              <button
                type="button"
                className="analyze-button"
                onClick={handleAnalyzeIncident}
                disabled={analysisLoading}
                aria-busy={analysisLoading}
              >
                {analysisLoading ? 'Analyzing...' : 'Analyze Incident'}
              </button>
            )}

            {analysis && (
              <div className="analysis-results">
                <section aria-labelledby="analysis-root-cause-heading">
                  <h3 id="analysis-root-cause-heading">Likely Root Cause</h3>
                  <p className="analysis-root-cause">{analysis.root_cause}</p>
                </section>

                <section aria-labelledby="analysis-confidence-heading">
                  <h3 id="analysis-confidence-heading">Confidence</h3>
                  <span
                    className={`confidence-badge confidence-${confidenceTone(analysis.confidence)}`}
                  >
                    {analysis.confidence}
                  </span>
                </section>

                <section aria-labelledby="analysis-evidence-heading">
                  <h3 id="analysis-evidence-heading">Evidence</h3>
                  {analysis.evidence.length > 0 ? (
                    <ul className="analysis-evidence">
                      {analysis.evidence.map((item, index) => (
                        <li key={`${index}-${item}`}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="analysis-empty">No evidence was returned.</p>
                  )}
                </section>

                <section aria-labelledby="analysis-actions-heading">
                  <h3 id="analysis-actions-heading">Recommended Actions</h3>
                  {analysis.recommended_actions.length > 0 ? (
                    <ol className="analysis-actions">
                      {analysis.recommended_actions.map((item, index) => (
                        <li key={`${index}-${item}`}>{item}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="analysis-empty">
                      No recommended actions were returned.
                    </p>
                  )}
                </section>
              </div>
            )}
          </section>
          )}

          {isEngineer && (
          <section
            className="similar-panel"
            aria-labelledby="similar-incidents-heading"
          >
            <div className="similar-panel-header">
              <div>
                <h2 id="similar-incidents-heading">Similar Historical Incidents</h2>
                {!similarIncidentsLoaded && (
                  <p className="similar-intro">
                    Compare this incident with previous incidents to identify
                    recurring operational patterns.
                  </p>
                )}
              </div>
              {similarIncidentsLoaded && (
                <button
                  type="button"
                  className="similar-refresh-button"
                  onClick={handleFindSimilarIncidents}
                  disabled={similarIncidentsLoading}
                  aria-busy={similarIncidentsLoading}
                >
                  {similarIncidentsLoading
                    ? 'Finding similar incidents...'
                    : 'Refresh Similar Incidents'}
                </button>
              )}
            </div>

            {similarIncidentsError && (
              <p className="similar-error" role="alert">
                {similarIncidentsError}
              </p>
            )}

            {similarIncidentsLoading && (
              <div className="similar-loading-block" aria-live="polite">
                <p className="similar-loading">Finding similar incidents...</p>
                <div className="skeleton-similar" aria-hidden="true">
                  <span className="skeleton" />
                  <span className="skeleton" />
                </div>
              </div>
            )}

            {!similarIncidentsLoaded && (
              <button
                type="button"
                className="similar-find-button"
                onClick={handleFindSimilarIncidents}
                disabled={similarIncidentsLoading}
                aria-busy={similarIncidentsLoading}
              >
                {similarIncidentsLoading
                  ? 'Finding similar incidents...'
                  : 'Find Similar Incidents'}
              </button>
            )}

            {similarIncidentsLoaded && similarIncidents.length === 0 && (
              <p className="similar-empty">
                No meaningfully similar historical incidents were found.
              </p>
            )}

            {similarIncidentsLoaded && similarIncidents.length > 0 && (
              <ul className="similar-list">
                {similarIncidents.map((item) => (
                  <li key={item.incident_id}>
                    <article className="similar-card">
                      <h3>{item.title}</h3>
                      <p className="similar-service">{item.service}</p>
                      <div className="similar-badges">
                        <span
                          className={`severity-badge severity-${item.severity}`}
                        >
                          {item.severity}
                        </span>
                        <span className={`status-badge status-${item.status}`}>
                          {item.status}
                        </span>
                        <span
                          className={`similarity-badge similarity-${similarityTone(item.similarity)}`}
                        >
                          {item.similarity}
                        </span>
                      </div>
                      <p className="similar-reason">{item.reason}</p>
                      <div className="similar-pattern">
                        <h4>Relevant Pattern</h4>
                        <p>{item.relevant_pattern}</p>
                      </div>
                    </article>
                  </li>
                ))}
              </ul>
            )}
          </section>
          )}

          <section className="timeline-section" aria-labelledby="incident-timeline-heading">
            <div className="section-heading timeline-heading">
              <h2 id="incident-timeline-heading">Incident Timeline</h2>
              {isEngineer && !addLogsOpen && (
                <button
                  type="button"
                  className="add-logs-button"
                  onClick={() => setAddLogsOpen(true)}
                  disabled={logsLoading}
                >
                  Add Logs
                </button>
              )}
            </div>

            {isEngineer && addLogsOpen && (
              <form className="add-logs-form" onSubmit={handleAddLogs}>
                {addLogsError && (
                  <p className="form-error" role="alert">
                    {addLogsError}
                  </p>
                )}

                {logDrafts.map((draft, index) => (
                  <fieldset
                    key={draft.key}
                    className="log-draft"
                    disabled={addLogsLoading}
                  >
                    <legend>Log {index + 1}</legend>
                    <div className="log-draft-fields">
                      <div className="form-field">
                        <label
                          className="form-label"
                          htmlFor={`log-level-${draft.key}`}
                        >
                          Level
                        </label>
                        <select
                          id={`log-level-${draft.key}`}
                          className="form-select"
                          value={draft.level}
                          onChange={(event) =>
                            updateLogDraft(draft.key, 'level', event.target.value)
                          }
                        >
                          <option value="DEBUG">DEBUG</option>
                          <option value="INFO">INFO</option>
                          <option value="WARN">WARN</option>
                          <option value="ERROR">ERROR</option>
                          <option value="CRITICAL">CRITICAL</option>
                        </select>
                      </div>
                      <div className="form-field">
                        <label
                          className="form-label"
                          htmlFor={`log-source-${draft.key}`}
                        >
                          Source
                        </label>
                        <input
                          id={`log-source-${draft.key}`}
                          className="form-input"
                          type="text"
                          value={draft.source}
                          onChange={(event) =>
                            updateLogDraft(draft.key, 'source', event.target.value)
                          }
                          required
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label
                        className="form-label"
                        htmlFor={`log-message-${draft.key}`}
                      >
                        Message
                      </label>
                      <textarea
                        id={`log-message-${draft.key}`}
                        className="form-textarea log-draft-message"
                        value={draft.message}
                        onChange={(event) =>
                          updateLogDraft(draft.key, 'message', event.target.value)
                        }
                        required
                      />
                    </div>
                    {logDrafts.length > 1 && (
                      <button
                        type="button"
                        className="remove-log-button"
                        onClick={() => removeLogDraft(draft.key)}
                      >
                        Remove
                      </button>
                    )}
                  </fieldset>
                ))}

                <button
                  type="button"
                  className="add-another-log-button"
                  onClick={addLogDraft}
                  disabled={addLogsLoading}
                >
                  + Add another log
                </button>

                <div className="form-actions">
                  <button
                    type="button"
                    className="form-cancel-button"
                    onClick={resetAddLogsForm}
                    disabled={addLogsLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="form-submit-button"
                    disabled={addLogsLoading}
                  >
                    {addLogsLoading ? 'Adding...' : 'Add Logs'}
                  </button>
                </div>
              </form>
            )}

            {logsLoading && (
              <div className="loading-block" aria-busy="true">
                <p className="state-message">Loading incident logs...</p>
                <div className="skeleton-list" aria-hidden="true">
                  <span className="skeleton" />
                  <span className="skeleton" />
                  <span className="skeleton" />
                </div>
              </div>
            )}

            {!logsLoading && logsError && (
              <p className="state-message error">{logsError}</p>
            )}

            {!logsLoading && !logsError && logs.length === 0 && (
              <p className="state-message">No logs recorded for this incident.</p>
            )}

            {!logsLoading && !logsError && logs.length > 0 && (
              <ol className="timeline">
                {logs.map((log) => (
                  <li
                    key={log.id}
                    className={`timeline-entry log-level-${log.level.toLowerCase()}`}
                  >
                    <div className="timeline-rail" aria-hidden="true">
                      <span className="timeline-dot" />
                    </div>
                    <div className="timeline-card">
                      <div className="timeline-meta">
                        <time dateTime={log.timestamp}>
                          {formatTimestamp(log.timestamp)}
                        </time>
                        <span
                          className={`log-level log-level-${log.level.toLowerCase()}`}
                        >
                          {log.level}
                        </span>
                        <span className="log-source">{log.source}</span>
                      </div>
                      <p className="log-message">{log.message}</p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </article>
      </AppShell>
    )
  }

  return (
    <AppShell
      user={user}
      isEngineer={isEngineer}
      viewingIncident={false}
      onShowIncidents={leaveIncident}
      onLogout={onLogout}
      onNewIncident={() => setCreateFormOpen(true)}
    >
      <header className="page-heading">
        <div>
          <p className="eyebrow">Live operational view</p>
          <h1>Incidents</h1>
          <p className="subtitle">
            Current and recent incidents, with severity, service, and status.
          </p>
        </div>
      </header>

      {isEngineer && createFormOpen && (
        <section
          className="create-incident-panel"
          aria-labelledby="create-incident-heading"
        >
          <h2 id="create-incident-heading">Create incident</h2>
          {createError && (
            <p className="form-error" role="alert">
              {createError}
            </p>
          )}
          <form className="create-incident-form" onSubmit={handleCreateIncident}>
            <div className="form-field">
              <label className="form-label" htmlFor="incident-title">
                Title
              </label>
              <input
                id="incident-title"
                className="form-input"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                disabled={createLoading}
              />
            </div>

            <div className="form-row">
              <div className="form-field">
                <label className="form-label" htmlFor="incident-service">
                  Service
                </label>
                <input
                  id="incident-service"
                  className="form-input"
                  type="text"
                  value={service}
                  onChange={(event) => setService(event.target.value)}
                  placeholder="citizen-services-api"
                  required
                  disabled={createLoading}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="incident-severity">
                  Severity
                </label>
                <select
                  id="incident-severity"
                  className="form-select"
                  value={severity}
                  onChange={(event) => setSeverity(event.target.value)}
                  disabled={createLoading}
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="critical">critical</option>
                </select>
              </div>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="incident-description">
                Description
              </label>
              <textarea
                id="incident-description"
                className="form-textarea"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                required
                disabled={createLoading}
              />
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="form-cancel-button"
                onClick={resetCreateForm}
                disabled={createLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="form-submit-button"
                disabled={createLoading}
              >
                {createLoading ? 'Creating...' : 'Create Incident'}
              </button>
            </div>
          </form>
        </section>
      )}

      {loading && (
        <div className="loading-block" aria-busy="true">
          <p className="state-message">Loading incidents...</p>
          <div className="skeleton-metrics" aria-hidden="true">
            <span className="skeleton" />
            <span className="skeleton" />
            <span className="skeleton" />
            <span className="skeleton" />
          </div>
          <div className="skeleton-list" aria-hidden="true">
            <span className="skeleton" />
            <span className="skeleton" />
            <span className="skeleton" />
          </div>
        </div>
      )}
      {error && <p className="state-message error">{error}</p>}

      {!loading && !error && (
        <>
          <section className="metrics" aria-label="Incident metrics">
            <article className="metric-card">
              <p className="metric-label">Total incidents</p>
              <p className="metric-value">{totalIncidents}</p>
            </article>
            <article className="metric-card">
              <p className="metric-label">Active</p>
              <p className="metric-value">{activeIncidents}</p>
            </article>
            <article className="metric-card metric-card-critical">
              <p className="metric-label">Critical</p>
              <p className="metric-value">{criticalIncidents}</p>
            </article>
            <article className="metric-card">
              <p className="metric-label">Investigating</p>
              <p className="metric-value">{investigatingIncidents}</p>
            </article>
          </section>

          <section className="incidents-section" aria-label="Incident list">
            {incidents.length === 0 ? (
              <div className="empty-state">
                <h3>No incidents right now</h3>
                <p>
                  When something breaks, it will show up here with severity,
                  service, and status.
                </p>
              </div>
            ) : (
              <ul className="incident-list">
                {incidents.map((incident) => (
                  <li key={incident.id}>
                    <button
                      type="button"
                      className="incident-card"
                      data-severity={incident.severity}
                      onClick={() => handleSelectIncident(incident)}
                    >
                    <div className="incident-main">
                      <span
                        className={`severity-badge severity-${incident.severity}`}
                      >
                        {incident.severity}
                      </span>
                      <div className="incident-copy">
                        <h3>{incident.title}</h3>
                        <p className="incident-service">{incident.service}</p>
                      </div>
                    </div>
                    <div className="incident-meta">
                      <span
                        className={`status-badge status-${incident.status}`}
                      >
                        {incident.status}
                      </span>
                      <time dateTime={incident.created_at}>
                        {formatTimestamp(incident.created_at)}
                      </time>
                    </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </AppShell>
  )
}

function App() {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated || user === null) {
    return <AuthScreen />
  }

  return <Dashboard user={user} onLogout={logout} />
}

export default App
