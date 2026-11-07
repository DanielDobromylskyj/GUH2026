import type {
  TrendPoint,
  VenueDetail,
  VenueStatus,
  VenueSummary,
  VenueTrend,
} from './types'
import { HOURS, statusFromRatio } from './types'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '/api').replace(/\/$/, '')

/** Used when the backend is unreachable so the UI stays demoable. */
const MOCK_VENUES: VenueDetail[] = [
  { name: 'kdfasdf', capacity: 18, maxCapacity: 60, live: false, scanning: false },
  { name: 'Kilburn: LF1', capacity: 43, maxCapacity: 440, live: false, scanning: false },
  { name: 'lorum', capacity: 96, maxCapacity: 120, live: false, scanning: false },
  { name: 'ipsum', capacity: 55, maxCapacity: 100, live: false, scanning: false },
  { name: 'delmut', capacity: 7, maxCapacity: 250, live: false, scanning: false },
]

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    signal,
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) throw new Error(`${path} responded ${res.status}`)
  return (await res.json()) as T
}

function normaliseStatus(value: unknown): VenueStatus {
  const raw = String(value ?? '').toLowerCase()
  if (raw === 'busy' || raw === 'full' || raw === 'high') return 'busy'
  if (raw === 'mid' || raw === 'moderate' || raw === 'medium') return 'mid'
  return 'empty'
}

function normaliseSummary(entry: unknown): VenueSummary {
  if (typeof entry === 'string') return { name: entry, status: 'empty', live: false }
  const obj = (entry ?? {}) as Record<string, unknown>
  return {
    name: String(obj.name ?? obj.venue ?? obj.id ?? 'Unknown'),
    status: normaliseStatus(obj.status),
    live: Boolean(obj.live),
  }
}

function normaliseDetail(name: string, payload: unknown): VenueDetail {
  const obj = (payload ?? {}) as Record<string, unknown>
  const capacity = Number(obj.capacity ?? obj.occupancy ?? obj.count ?? 0)
  const maxCapacity = Number(
    obj.maxCapacity ?? obj.max_capacity ?? obj.max ?? obj.limit ?? 0,
  )
  return {
    name: String(obj.name ?? name),
    capacity: Number.isFinite(capacity) ? capacity : 0,
    maxCapacity: Number.isFinite(maxCapacity) ? maxCapacity : 0,
    live: Boolean(obj.live),
    scanning: Boolean(obj.scanning),
  }
}

export interface VenuesResult {
  venues: VenueSummary[]
  usingMockData: boolean
}

export async function fetchVenues(signal?: AbortSignal): Promise<VenuesResult> {
  try {
    const data = await getJson<unknown>('/venues', signal)
    const list = Array.isArray(data)
      ? data
      : ((data as Record<string, unknown>)?.venues as unknown[]) ?? []
    const venues = list.map(normaliseSummary).filter((v) => v.name)
    if (venues.length === 0) throw new Error('empty venue list')
    return { venues, usingMockData: false }
  } catch (err) {
    if (signal?.aborted) throw err
    return {
      venues: MOCK_VENUES.map((v) => ({
        name: v.name,
        status: statusFromRatio(v.capacity / Math.max(v.maxCapacity, 1)),
        live: false,
      })),
      usingMockData: true,
    }
  }
}

export async function fetchVenueDetail(
  name: string,
  signal?: AbortSignal,
): Promise<VenueDetail> {
  try {
    const data = await getJson<unknown>(
      `/venues/${encodeURIComponent(name)}`,
      signal,
    )
    return normaliseDetail(name, data)
  } catch (err) {
    if (signal?.aborted) throw err
    const mock = MOCK_VENUES.find((v) => v.name === name)
    return (
      mock ?? { name, capacity: 0, maxCapacity: 0, live: false, scanning: false }
    )
  }
}

/** Hourly averages over the last `days` days, padded to every opening hour. */
export async function fetchVenueTrend(
  name: string,
  days = 7,
  signal?: AbortSignal,
): Promise<VenueTrend> {
  const empty: VenueTrend = {
    points: HOURS.map((hour) => ({ hour, capacity: 0 })),
    maxCapacity: 0,
    hasData: false,
  }

  try {
    const data = await getJson<unknown>(
      `/venues/${encodeURIComponent(name)}/averages?days=${days}`,
      signal,
    )
    const obj = (data ?? {}) as Record<string, unknown>
    const raw = Array.isArray(obj.averages) ? obj.averages : []

    const byHour = new Map<string, number>()
    for (const item of raw as Record<string, unknown>[]) {
      const hour = String(item?.hour ?? '')
      const capacity = Number(item?.capacity ?? 0)
      if (hour) byHour.set(hour, Number.isFinite(capacity) ? capacity : 0)
    }

    const points: TrendPoint[] = HOURS.map((hour) => ({
      hour,
      capacity: byHour.get(hour) ?? 0,
    }))
    const maxCapacity = Number(obj.max_capacity ?? 0)

    return {
      points,
      maxCapacity: Number.isFinite(maxCapacity) ? maxCapacity : 0,
      hasData: byHour.size > 0,
    }
  } catch (err) {
    if (signal?.aborted) throw err
    return empty
  }
}
