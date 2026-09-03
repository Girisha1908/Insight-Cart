/**
 * Shared base API client for the InsightCart frontend.
 *
 * All feature-specific services (customerApi, productApi, businessApi,
 * opportunityApi) should use this module rather than calling fetch directly,
 * so error handling and the base URL stay consistent project-wide.
 */

const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

export class ApiError extends Error {
  status: number
  detail?: string

  constructor(status: number, detail?: string) {
    super(detail ?? `Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    let detail: string | undefined
    try {
      const body = (await res.json()) as { detail?: string }
      detail = body.detail
    } catch {
      // no JSON body; use statusText
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) {
    return undefined as T
  }
  return (await res.json()) as T
}

export default apiFetch
