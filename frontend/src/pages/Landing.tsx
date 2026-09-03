import { useEffect, useState } from 'react'
import { apiFetch } from '../services/api'

interface HealthResponse {
  status: string
  environment: string
}

export default function Landing() {
  const [health, setHealth] = useState<HealthResponse | null>(null)

  useEffect(() => {
    apiFetch<HealthResponse>('/health')
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-slate-50 text-slate-800">
      <h1 className="text-4xl font-bold">🛒 InsightCart</h1>
      <p className="text-slate-500">E-commerce decision intelligence platform</p>
      <div className="rounded-lg border border-slate-200 bg-white px-6 py-4 shadow-sm">
        {health ? (
          <p className="text-sm text-emerald-600">
            API status: <span className="font-semibold">{health.status}</span>
            {' · '}environment: <span className="font-semibold">{health.environment}</span>
          </p>
        ) : (
          <p className="text-sm text-slate-400">Waiting for API…</p>
        )}
      </div>
    </div>
  )
}
