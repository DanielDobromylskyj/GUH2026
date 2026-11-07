import { useEffect, useState } from 'react'
import { fetchVenueTrend } from '../lib/api'
import type { VenueTrend } from '../lib/types'
import { STATUS_META, statusFromRatio } from '../lib/types'

interface Props {
  venue: string | null
  days?: number
}

/** Average occupancy per opening hour, drawn from stored history. */
export function OccupancyTrend({ venue, days = 7 }: Props) {
  const [trend, setTrend] = useState<VenueTrend | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!venue) {
      setTrend(null)
      return
    }
    const controller = new AbortController()

    const load = async () => {
      setLoading(true)
      try {
        setTrend(await fetchVenueTrend(venue, days, controller.signal))
      } catch {
        /* aborted */
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    void load()
    return () => controller.abort()
  }, [venue, days])

  const points = trend?.points ?? []
  const peak = Math.max(
    trend?.maxCapacity ?? 0,
    ...points.map((p) => p.capacity),
    1,
  )

  return (
    <section className="card trend">
      <div className="card__head">
        <h2 className="card__title">Occupancy trend</h2>
        <span className="trend__meta">Average by hour · last {days} days</span>
      </div>

      {trend && !trend.hasData && !loading && (
        <p className="card__hint">
          No readings recorded yet — check back once this venue has been
          sampled.
        </p>
      )}

      <div className="trend__chart" role="img" aria-label="Occupancy by hour">
        <div className="trend__grid" aria-hidden="true">
          {[1, 0.75, 0.5, 0.25, 0].map((f) => (
            <span key={f} className="trend__gridline">
              <em>{Math.round(peak * f)}</em>
            </span>
          ))}
        </div>

        <ol className="trend__bars">
          {points.map((point) => {
            const ratio = point.capacity / peak
            const status = statusFromRatio(
              point.capacity / Math.max(trend?.maxCapacity ?? peak, 1),
            )
            return (
              <li key={point.hour} className="trend__bar">
                <span
                  className="trend__fill"
                  style={{
                    height: `${Math.max(ratio * 100, point.capacity > 0 ? 2 : 0)}%`,
                    background: STATUS_META[status].colour,
                  }}
                  title={`${point.hour}: ${Math.round(point.capacity)} people`}
                />
                <span className="trend__hour">{point.hour}</span>
              </li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}
