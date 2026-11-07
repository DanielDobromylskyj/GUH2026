import { useBluetoothScan } from '../hooks/useBluetoothScan'

const STATE_TEXT: Record<string, string> = {
  idle: 'Scanner idle',
  scanning: 'Scanning nearby devices',
  unsupported: 'Web Bluetooth unavailable',
  denied: 'Scan permission denied',
}

export function BluetoothEstimator() {
  const {
    devices,
    state,
    usingMockDevices,
    estimatedPeople,
    startScan,
    stopScan,
  } = useBluetoothScan()
  const scanning = state !== 'idle'

  return (
    <section className="card scanner">
      <div className="card__head">
        <h2 className="card__title">Bluetooth estimator</h2>
        <button
          type="button"
          className={`btn${scanning ? ' btn--stop' : ''}`}
          onClick={scanning ? stopScan : startScan}
        >
          {scanning ? 'Stop scan' : 'Start scan'}
        </button>
      </div>

      <p className="card__hint">
        {STATE_TEXT[state] ?? state}
        {usingMockDevices && ' — simulated feed'}
      </p>

      <div className="scanner__stats">
        <div>
          <span className="scanner__num">{devices.length}</span>
          <span className="scanner__cap">devices seen</span>
        </div>
        <div>
          <span className="scanner__num">{estimatedPeople}</span>
          <span className="scanner__cap">estimated people</span>
        </div>
      </div>

      <ul className="rssi-list">
        {devices.slice(0, 6).map((device) => (
          <li key={device.id}>
            <span className="rssi-list__name">{device.name}</span>
            <span className="rssi-list__bar">
              <span
                style={{
                  width: `${Math.min(
                    Math.max((device.rssi + 100) * 1.4, 4),
                    100,
                  )}%`,
                }}
              />
            </span>
            <span className="rssi-list__val">{device.rssi} dBm</span>
          </li>
        ))}
        {devices.length === 0 && (
          <li className="rssi-list__empty">No devices detected yet.</li>
        )}
      </ul>
    </section>
  )
}
