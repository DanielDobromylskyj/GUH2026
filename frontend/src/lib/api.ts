import type { VenueDetail, VenueStatus, VenueSummary } from './types'
import { statusFromRatio } from './types'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '/api').replace(/\/$/, '')

/** Used when the backend is unreachable so the UI stays demoable. */
const MOCK_VENUES: VenueDetail[] = [
  { name: 'kdfasdf', capacity: 18, maxCapacity: 60 },
  { name: 'Kilburn: LF1', capacity: 43, maxCapacity: 440 },
  { name: 'lorum', capacity: 96, maxCapacity: 120 },
  { name: 'ipsum', capacity: 55, maxCapacity: 100 },
  { name: 'delmut', capacity: 7, maxCapacity: 250 },
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
  if (typeof entry === 'string') return { name: entry, status: 'empty' }
  const obj = (entry ?? {}) as Record<string, unknown>
  return {
    name: String(obj.name ?? obj.venue ?? obj.id ?? 'Unknown'),
    status: normaliseStatus(obj.status),
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
    return mock ?? { name, capacity: 0, maxCapacity: 0 }
  }
}
