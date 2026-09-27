import type { components } from './api.generated'

export type SystemStatus = components['schemas']['SystemStatus']

export async function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  const response = await fetch('/api/v1/system/status', { signal, credentials: 'same-origin' })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  const payload: unknown = await response.json()
  if (
    typeof payload !== 'object' || payload === null ||
    !('service' in payload) || payload.service !== 'szurubooru-toolkit' ||
    !('mode' in payload) || payload.mode !== 'scaffold' ||
    !('operations_enabled' in payload) || payload.operations_enabled !== false ||
    !('static_ready' in payload) || typeof payload.static_ready !== 'boolean'
  ) throw new Error('Unexpected API response')
  return payload as SystemStatus
}