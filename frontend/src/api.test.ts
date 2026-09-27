import { afterEach, expect, it, vi } from 'vitest'
import { getSystemStatus } from './api'

afterEach(() => vi.unstubAllGlobals())

it('rejects a failed HTTP response', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })))
  await expect(getSystemStatus()).rejects.toThrow('503')
})

it('rejects a response that violates the scaffold contract', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ operations_enabled: true }))))
  await expect(getSystemStatus()).rejects.toThrow('Unexpected API response')
})