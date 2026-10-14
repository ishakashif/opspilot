export interface CountSegment {
  label: string
  count: number
  color: string
}

const FALLBACK_COLOR = '#8b95a8'

export function countSegments(
  values: string[],
  preferred: readonly string[],
  colors: Record<string, string>,
): CountSegment[] {
  const counts = new Map<string, number>()
  for (const name of preferred) {
    counts.set(name, 0)
  }
  for (const value of values) {
    const key = value.trim() || 'unknown'
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return [...counts.entries()].map(([label, count]) => ({
    label,
    count,
    color: colors[label] ?? FALLBACK_COLOR,
  }))
}

export function serviceSegments(
  services: string[],
): CountSegment[] {
  const counts = new Map<string, number>()
  for (const service of services) {
    const key = service.trim() || 'Unspecified service'
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([label, count]) => ({
      label,
      count,
      color: '#b794ff',
    }))
}

function panelCaption(segments: CountSegment[]) {
  const total = segments.reduce((sum, segment) => sum + segment.count, 0)
  if (total === 0) {
    return 'No incidents recorded yet.'
  }
  return segments
    .map((segment) => `${segment.count} ${segment.label}`)
    .join(', ')
}

export function DonutPanel({
  title,
  note,
  segments,
}: {
  title: string
  note: string
  segments: CountSegment[]
}) {
  const total = segments.reduce((sum, segment) => sum + segment.count, 0)
  const radius = 42
  const circumference = 2 * Math.PI * radius
  let offset = 0

  return (
    <section className="viz-panel" aria-labelledby="severity-chart-heading">
      <header className="viz-heading">
        <h2 id="severity-chart-heading">{title}</h2>
        <p>{note}</p>
      </header>
      {total === 0 ? (
        <p className="viz-empty">No incidents recorded yet.</p>
      ) : (
        <div className="donut-layout">
          <svg className="donut" viewBox="0 0 120 120" aria-hidden="true">
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="12"
            />
            {segments.map((segment) => {
              const length = (segment.count / total) * circumference
              const dash = `${length} ${circumference - length}`
              const dashOffset = -offset
              offset += length
              if (segment.count === 0) {
                return null
              }
              return (
                <circle
                  key={segment.label}
                  cx="60"
                  cy="60"
                  r={radius}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth="12"
                  strokeDasharray={dash}
                  strokeDashoffset={dashOffset}
                  strokeLinecap="butt"
                  transform="rotate(-90 60 60)"
                />
              )
            })}
            <text className="donut-total" x="60" y="58" textAnchor="middle">
              {total}
            </text>
            <text className="donut-unit" x="60" y="74" textAnchor="middle">
              total
            </text>
          </svg>
          <ul className="viz-legend">
            {segments.map((segment) => (
              <li key={segment.label}>
                <span
                  className="legend-swatch"
                  style={{ background: segment.color }}
                  aria-hidden="true"
                />
                <span className="legend-label">{segment.label}</span>
                <span className="legend-count">{segment.count}</span>
              </li>
            ))}
          </ul>
          <p className="sr-only">{panelCaption(segments)}</p>
        </div>
      )}
    </section>
  )
}

export function BarPanel({
  title,
  note,
  segments,
  headingId,
  preserveCase = false,
}: {
  title: string
  note: string
  segments: CountSegment[]
  headingId: string
  preserveCase?: boolean
}) {
  const max = Math.max(...segments.map((segment) => segment.count), 1)
  const total = segments.reduce((sum, segment) => sum + segment.count, 0)

  return (
    <section className="viz-panel" aria-labelledby={headingId}>
      <header className="viz-heading">
        <h2 id={headingId}>{title}</h2>
        <p>{note}</p>
      </header>
      {total === 0 ? (
        <p className="viz-empty">No incidents recorded yet.</p>
      ) : (
        <ul className={`bar-list${preserveCase ? ' is-raw' : ''}`}>
          {segments.map((segment) => (
            <li key={segment.label}>
              <div className="bar-label">
                <span>{segment.label}</span>
                <span className="legend-count">{segment.count}</span>
              </div>
              <div
                className="bar-track"
                role="presentation"
              >
                <span
                  className="bar-fill"
                  style={{
                    width: `${(segment.count / max) * 100}%`,
                    background: segment.color,
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
