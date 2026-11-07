export type VenueStatus = 'busy' | 'mid' | 'empty'

/** Shape returned by `GET /venues`. */
export interface VenueSummary {
  name: string
  status: VenueStatus
}

/** Shape returned by `GET /venues/{name}`. */
export interface VenueDetail {
  name: string
  capacity: number
  maxCapacity: number
}

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
