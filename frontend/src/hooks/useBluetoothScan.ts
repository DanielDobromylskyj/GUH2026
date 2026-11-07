import { useCallback, useEffect, useRef, useState } from 'react'

export interface ScannedDevice {
  id: string
  name: string
  rssi: number
  lastSeen: number
}

export type ScanState = 'idle' | 'scanning' | 'unsupported' | 'denied'

/**
 * Placeholder Bluetooth integration.
 *
 * Attempts to use the experimental Web Bluetooth scanning API
 * (`navigator.bluetooth.requestLEScan`). Where that is unavailable — which is
 * most browsers today — it falls back to a mock device feed so downstream
 * foot-traffic estimation can be developed against realistic data.
 */
export function useBluetoothScan() {
  const [devices, setDevices] = useState<ScannedDevice[]>([])
  const [state, setState] = useState<ScanState>('idle')
  const [usingMockDevices, setUsingMockDevices] = useState(false)
  const scanRef = useRef<{ stop: () => void } | null>(null)
  const timerRef = useRef<number | null>(null)

  const stopScan = useCallback(() => {
    scanRef.current?.stop()
    scanRef.current = null
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
    setState('idle')
  }, [])

  const startMockScan = useCallback(() => {
    setUsingMockDevices(true)
    setState('scanning')
    const tick = () => {
      const count = 6 + Math.floor(Math.random() * 7)
      setDevices(
        Array.from({ length: count }, (_, i) => ({
          id: `mock-${i}`,
          name: `Device ${String(i + 1).padStart(2, '0')}`,
          rssi: -45 - Math.floor(Math.random() * 45),
          lastSeen: Date.now(),
        })).sort((a, b) => b.rssi - a.rssi),
      )
    }
    tick()
    timerRef.current = window.setInterval(tick, 2500)
  }, [])

  const startScan = useCallback(async () => {
    const bluetooth = (
      navigator as Navigator & {
        bluetooth?: {
          requestLEScan?: (options: unknown) => Promise<{ stop: () => void }>
          addEventListener?: (
            type: string,
            listener: (event: Event) => void,
          ) => void
        }
      }
    ).bluetooth

    if (!bluetooth?.requestLEScan) {
      setState('unsupported')
      startMockScan()
      return
    }

    try {
      const scan = await bluetooth.requestLEScan({ acceptAllAdvertisements: true })
      scanRef.current = scan
      setUsingMockDevices(false)
      setState('scanning')
      bluetooth.addEventListener?.('advertisementreceived', (event: Event) => {
        const ad = event as Event & {
          device?: { id?: string; name?: string }
          rssi?: number
        }
        const id = ad.device?.id
        if (!id) return
        setDevices((prev) => {
          const next = prev.filter((d) => d.id !== id)
          next.push({
            id,
            name: ad.device?.name ?? 'Unknown device',
            rssi: ad.rssi ?? -100,
            lastSeen: Date.now(),
          })
          return next.sort((a, b) => b.rssi - a.rssi)
        })
      })
    } catch {
      setState('denied')
      startMockScan()
    }
  }, [startMockScan])

  useEffect(() => stopScan, [stopScan])

  /** Naive foot-traffic estimate: nearby devices weighted by signal strength. */
  const estimatedPeople = devices.reduce(
    (total, device) => total + (device.rssi > -70 ? 1 : 0.5),
    0,
  )

  return {
    devices,
    state,
    usingMockDevices,
    estimatedPeople: Math.round(estimatedPeople),
    startScan,
    stopScan,
  }
}
