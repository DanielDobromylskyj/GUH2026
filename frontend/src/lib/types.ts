export type VenueStatus = 'busy' | 'mid' | 'empty'

/** Shape returned by `GET /api/venues`. */
export interface VenueSummary {
  name: string
  status: VenueStatus
  live: boolean
}

/** Shape returned by `GET /api/venues/{name}`. */
export interface VenueDetail {
  name: string
  capacity: number
  maxCapacity: number
  live: boolean
  scanning: boolean
}

/** One bar of the occupancy trend chart. */
export interface TrendPoint {
  hour: string
  capacity: number
}

/** Shape returned by `GET /api/venues/{name}/averages`. */
export interface VenueTrend {
  points: TrendPoint[]
  maxCapacity: number
  hasData: boolean
}

/** Opening hours, matching `src/db/hours.py`. */
export const HOURS = [
  '8am', '9am', '10am', '11am', '12pm', '1pm',
  '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm',
] as const

export const STATUS_META: Record<
  VenueStatus,
  { label: string; colour: string }
> = {
  busy: { label: 'Very busy', colour: 'var(--busy)' },
  mid: { label: 'A bit busy', colour: 'var(--mid)' },
  empty: { label: 'Not busy', colour: 'var(--empty)' },
}

export function statusFromRatio(ratio: number): VenueStatus {
  if (ratio >= 0.75) return 'busy'
  if (ratio >= 0.4) return 'mid'
  return 'empty'
}
