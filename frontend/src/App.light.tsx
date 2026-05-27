import { useEffect, useState } from 'react'

const chartSvg = (data: number[]) => {
  if (!data || data.length === 0) return null
  const w = 300
  const h = 80
  const max = Math.max(...data)
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - (v / max) * h
    return `${x},${y}`
  })
  const path = `M ${points.join(' L ')}`
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <path d={path} fill="none" stroke="#2b6cb0" strokeWidth={2} />
    </svg>
  )
}

export default function AppLight() {
  const [scans, setScans] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [url, setUrl] = useState('')
  const apiBase = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

  useEffect(() => {
    const fetchRecent = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${apiBase}/recent`)
        if (res.ok) {
          const data = await res.json()
          setScans(data)
        } else {
          setScans([])
        }
      } catch (e) {
        setScans([])
      } finally {
        setLoading(false)
      }
    }
    fetchRecent()
  }, [])

  const startScan = async () => {
    if (!url) return alert('Enter a URL')
    try {
      await fetch(`${apiBase}/scan`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) })
      alert('Scan started')
      setScans((s) => [{ id: String(Date.now()), url, status: 'Queued', score: 0 }, ...s])
      setUrl('')
    } catch (e) {
      alert('Failed')
    }
  }

  const trend = scans.slice(0, 6).map((s) => s.score || 0)

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: 20 }}>
      <h1 style={{ color: '#1a202c' }}>PHANTOM — Lightweight</h1>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" style={{ flex: 1, padding: 8 }} />
        <button onClick={startScan} style={{ padding: '8px 12px' }}>Scan</button>
      </div>

      <div style={{ marginTop: 20, background: '#fff', padding: 12, borderRadius: 8 }}>
        <h3>Recent Scans</h3>
        {loading ? <div>Loading...</div> : (
          <ul>
            {scans.map((s) => (
              <li key={s.id} style={{ padding: '6px 0', borderBottom: '1px solid #eee' }}>{s.url} — {s.status} — {s.score}</li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ marginTop: 12 }}>
        <h4>Trend</h4>
        {chartSvg(trend)}
      </div>
    </div>
  )
}
