import { WORLD_LAND_PATH, WORLD_LINKS, WORLD_NODES } from './worldMapData.ts'

const GRATICULE_X = [0, 125, 250, 375, 500, 625, 750, 875, 1000]
const GRATICULE_Y = [0, 83, 166, 250, 333, 416, 500]

export default function AuthWorldMap() {
  return (
    <div className="auth-world" aria-hidden="true">
      <svg
        className="auth-world-svg"
        viewBox="0 0 1000 500"
        preserveAspectRatio="xMidYMid slice"
      >
        {GRATICULE_X.map((x) => (
          <line
            key={`gx-${x}`}
            className="auth-graticule"
            x1={x}
            y1={0}
            x2={x}
            y2={500}
          />
        ))}
        {GRATICULE_Y.map((y) => (
          <line
            key={`gy-${y}`}
            className="auth-graticule"
            x1={0}
            y1={y}
            x2={1000}
            y2={y}
          />
        ))}
        <path className="auth-land" d={WORLD_LAND_PATH} />
        {WORLD_LINKS.map((link) => (
          <path key={link.id} className="auth-link" d={link.d} />
        ))}
        {WORLD_LINKS.map((link) => (
          <path
            key={`${link.id}-pulse`}
            className="auth-link-pulse"
            d={link.d}
            style={{ animationDelay: `-${link.delay}s` }}
          />
        ))}
        {WORLD_NODES.map((node) => (
          <g key={node.id} transform={`translate(${node.x} ${node.y})`}>
            <circle className="auth-node-glow" r="4.4" />
            <circle className="auth-node" r="1.45" />
          </g>
        ))}
      </svg>
      <div className="auth-world-shade" />
    </div>
  )
}
