import type { VenueDetail } from '../lib/types'
import { STATUS_META, statusFromRatio } from '../lib/types'
import { BluetoothEstimator } from './BluetoothEstimator'

interface Props {
  detail: VenueDetail | null
  loading: boolean
}

export function VenueDetailPanel({ detail, loading }: Props) {
  if (!detail) {
    return (
      <main className="panel">
        <div className="card card--placeholder">
          {loading ? 'Loading venue…' : 'Select a venue to see live capacity.'}
        </div>
      </main>
    )
  }

  const max = Math.max(detail.maxCapacity, 1)
  const ratio = Math.min(detail.capacity / max, 1)
  const status = statusFromRatio(ratio)
  const meta = STATUS_META[status]

  return (
    <main className="panel">
      <header className="panel__head">
        <div>
          <p className="panel__eyebrow">Live occupancy</p>
          <h1 className="panel__title">{detail.name}</h1>
        </div>
        <span className="status-pill" style={{ background: meta.colour }}>
          {meta.label}
        </span>
      </header>

      <section className="card capacity">
        <div className="capacity__row">
          <h2 className="capacity__label">Capacity</h2>
          <p className="capacity__value">
            {detail.capacity}
            <span className="capacity__max">/{detail.maxCapacity}</span>
          </p>
        </div>
        <div
          className="capacity__bar"
          role="progressbar"
          aria-valuenow={detail.capacity}
          aria-valuemin={0}
          aria-valuemax={detail.maxCapacity}
        >
          <div
            className="capacity__fill"
            style={{ width: `${ratio * 100}%`, background: meta.colour }}
          />
        </div>
        <p className="capacity__hint">
          {Math.round(ratio * 100)}% full ·{' '}
          {Math.max(detail.maxCapacity - detail.capacity, 0)} spaces left
        </p>
      </section>

      <div className="panel__grid">
        <BluetoothEstimator />
        <section className="card card--future">
          <h2 className="card__title">Occupancy trend</h2>
          <p className="card__hint">
            Reserved for charts and scanner logs.
          </p>
          <div className="chart-placeholder" aria-hidden="true">
            {[32, 48, 26, 64, 55, 78, 41].map((h, i) => (
              <span key={i} style={{ height: `${h}%` }} />
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
