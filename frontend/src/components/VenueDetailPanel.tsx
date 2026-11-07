import type { VenueDetail } from '../lib/types'
import { STATUS_META, statusFromRatio } from '../lib/types'
import { OccupancyTrend } from './OccupancyTrend'

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
          <h1 className="panel__title">
            {detail.name}
            {detail.live && (
              <span
                className={`live-dot${detail.scanning ? '' : ' live-dot--off'}`}
                title={
                  detail.scanning
                    ? 'Bluetooth scanner running'
                    : 'Bluetooth scanner unavailable'
                }
              >
                ● live
              </span>
            )}
          </h1>
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
        <div className="capacity__footer">
          <p className="capacity__hint">
            {Math.round(ratio * 100)}% full ·{' '}
            {Math.max(detail.maxCapacity - detail.capacity, 0)} spaces left
          </p>
          <p
            className="capacity__devices"
            title="Raw number of tracked Bluetooth devices"
          >
            {detail.devices} device{detail.devices === 1 ? '' : 's'} tracked
          </p>
        </div>
      </section>

      <OccupancyTrend venue={detail.name} />
    </main>
  )
}
