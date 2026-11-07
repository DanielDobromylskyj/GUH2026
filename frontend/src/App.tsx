import { useEffect, useState } from 'react'
import { VenueSidebar } from './components/VenueSidebar'
import { VenueDetailPanel } from './components/VenueDetailPanel'
import { fetchVenueDetail, fetchVenues } from './lib/api'
import type { VenueDetail, VenueSummary } from './lib/types'
import './App.css'

const REFRESH_MS = 15000

function App() {
  const [venues, setVenues] = useState<VenueSummary[]>([])
  const [venuesLoading, setVenuesLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<{
    requested: string
    data: VenueDetail
  } | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    const load = async () => {
      try {
        const { venues: list, usingMockData } = await fetchVenues(
          controller.signal,
        )
        setVenues(list)
        setOffline(usingMockData)
        setSelected((current) =>
          current && list.some((v) => v.name === current)
            ? current
            : list.find((v) => v.name === 'Kilburn: LF1')?.name ??
              list[0]?.name ??
              null,
        )
      } finally {
        if (!controller.signal.aborted) setVenuesLoading(false)
      }
    }

    void load()
    const timer = window.setInterval(load, REFRESH_MS)
    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    if (!selected) return
    const controller = new AbortController()

    const load = async () => {
      setDetailLoading(true)
      try {
        const data = await fetchVenueDetail(selected, controller.signal)
        setDetail({ requested: selected, data })
      } catch {
        /* aborted */
      } finally {
        if (!controller.signal.aborted) setDetailLoading(false)
      }
    }

    void load()
    const timer = window.setInterval(load, REFRESH_MS)
    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [selected])

  return (
    <div className="app">
      <header className="topbar">
        <button
          type="button"
          className="topbar__toggle"
          aria-expanded={sidebarOpen}
          onClick={() => setSidebarOpen((open) => !open)}
        >
          ☰ Venues
        </button>
        <span className="topbar__brand">Capacity Checker</span>
        {offline && <span className="topbar__badge">demo data</span>}
      </header>

      <div className={`layout${sidebarOpen ? ' layout--open' : ''}`}>
        <VenueSidebar
          venues={venues}
          selected={selected}
          loading={venuesLoading}
          onSelect={(name) => {
            setSelected(name)
            setSidebarOpen(false)
          }}
        />
        <VenueDetailPanel
          detail={detail?.requested === selected ? detail.data : null}
          loading={detailLoading || venuesLoading}
        />
      </div>
    </div>
  )
}

export default App
