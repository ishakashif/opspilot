import { useEffect, useState } from 'react'
import './App.css'

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

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString()
}

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/incidents/')
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

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="brand-mark">Incident operations</p>
          <h1>OpsPilot</h1>
          <p className="subtitle">Intelligent Incident Operations</p>
        </div>
      </header>

      {loading && <p className="state-message">Loading incidents...</p>}
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

          <section className="incidents-section">
            <div className="section-heading">
              <h2>Incidents</h2>
              <p>Live operational view of current and recent incidents.</p>
            </div>

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
                  <li key={incident.id} className="incident-card">
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
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}

export default App
