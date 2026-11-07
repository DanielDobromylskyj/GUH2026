import type { VenueSummary } from '../lib/types'
import { STATUS_META } from '../lib/types'

interface Props {
  venues: VenueSummary[]
  selected: string | null
  loading: boolean
  onSelect: (name: string) => void
}

export function VenueSidebar({ venues, selected, loading, onSelect }: Props) {
  return (
    <aside className="sidebar" aria-label="Venue selector">
      <div className="sidebar__head">
        <h2 className="sidebar__title">Venues</h2>
        <p className="sidebar__subtitle">
          {loading ? 'Loading…' : `${venues.length} tracked`}
        </p>
      </div>

      <ul className="venue-list">
        {venues.map((venue) => {
          const meta = STATUS_META[venue.status]
          const isActive = venue.name === selected
          return (
            <li key={venue.name}>
              <button
                type="button"
                className={`venue-card${isActive ? ' venue-card--active' : ''}`}
                aria-current={isActive ? 'true' : undefined}
                onClick={() => onSelect(venue.name)}
              >
                <span className="venue-card__name">
                  {venue.name}
                  {venue.live && <span className="venue-card__live">live</span>}
                </span>
                <span
                  className="venue-card__dot"
                  style={{ background: meta.colour }}
                  title={meta.label}
                  aria-label={meta.label}
                  role="img"
                />
              </button>
            </li>
          )
        })}
        {!loading && venues.length === 0 && (
          <li className="venue-list__empty">No venues available.</li>
        )}
      </ul>

      <ul className="legend">
        {(Object.keys(STATUS_META) as (keyof typeof STATUS_META)[]).map((k) => (
          <li key={k}>
            <span
              className="legend__dot"
              style={{ background: STATUS_META[k].colour }}
            />
            {STATUS_META[k].label}
          </li>
        ))}
      </ul>
    </aside>
  )
}
