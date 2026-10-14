import { useEffect, useRef } from 'react'
import createGlobe from 'cobe'

const MERIDIANS = [0, 30, 60, 90, 120, 150]
const PARALLELS = [
  { top: '6%', height: '88%' },
  { top: '18%', height: '64%' },
  { top: '32%', height: '36%' },
]

function webglAvailable() {
  try {
    const probe = document.createElement('canvas')
    return Boolean(
      probe.getContext('webgl') || probe.getContext('experimental-webgl'),
    )
  } catch {
    return false
  }
}

export default function DashboardGlobe() {
  const frameRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const frame = frameRef.current
    const canvas = canvasRef.current
    const grid = gridRef.current
    if (!frame || !grid) {
      return
    }

    const reduced = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches
    let phi = 0.55
    let raf = 0

    const paintGrid = () => {
      grid.style.transform = `rotateX(-16deg) rotateY(${phi}rad)`
    }

    if (!canvas || !webglAvailable()) {
      frame.dataset.globe = 'fallback'
      paintGrid()
      if (reduced) {
        return
      }
      const spin = () => {
        phi += 0.0016
        paintGrid()
        raf = requestAnimationFrame(spin)
      }
      raf = requestAnimationFrame(spin)
      return () => cancelAnimationFrame(raf)
    }

    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2)
    const measure = () => ({
      width: Math.max(frame.clientWidth, 1),
      height: Math.max(frame.clientHeight, 1),
    })

    let globe: ReturnType<typeof createGlobe>
    try {
      const initial = measure()
      globe = createGlobe(canvas, {
        devicePixelRatio: pixelRatio,
        width: initial.width,
        height: initial.height,
        phi,
        theta: 0.26,
        dark: 1,
        diffuse: 1.35,
        mapSamples: 12000,
        mapBrightness: 7.5,
        mapBaseBrightness: 0.04,
        baseColor: [0.15, 0.1, 0.36],
        markerColor: [0.62, 0.52, 1],
        glowColor: [0.4, 0.28, 0.95],
        markers: [],
        scale: 1,
        opacity: 0.94,
      })
    } catch {
      frame.dataset.globe = 'fallback'
      return
    }

    const render = () => {
      if (!reduced) {
        phi += 0.0016
      }
      paintGrid()
      const next = measure()
      globe.update({
        phi,
        theta: 0.26,
        width: next.width,
        height: next.height,
      })
      if (!reduced) {
        raf = requestAnimationFrame(render)
      }
    }
    render()

    const observer = new ResizeObserver(() => {
      const next = measure()
      globe.update({
        phi,
        width: next.width,
        height: next.height,
      })
    })
    observer.observe(frame)

    return () => {
      cancelAnimationFrame(raf)
      observer.disconnect()
      globe.destroy()
    }
  }, [])

  return (
    <div className="dashboard-globe" ref={frameRef} aria-hidden="true">
      <canvas ref={canvasRef} className="globe-canvas" />
      <div className="globe-fallback" />
      <div className="globe-graticule" ref={gridRef}>
        {MERIDIANS.map((degrees) => (
          <span
            key={`meridian-${degrees}`}
            className="globe-line"
            style={{ transform: `rotateY(${degrees}deg)` }}
          />
        ))}
        {PARALLELS.map((band) => (
          <span
            key={`parallel-${band.top}`}
            className="globe-line globe-parallel"
            style={{ top: band.top, height: band.height }}
          />
        ))}
      </div>
    </div>
  )
}
