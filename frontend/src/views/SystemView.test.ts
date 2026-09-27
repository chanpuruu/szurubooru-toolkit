import { flushPromises, mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import PrimeVue from 'primevue/config'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SystemView from './SystemView.vue'

afterEach(() => vi.unstubAllGlobals())

function renderView() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  const wrapper = mount(SystemView, { global: { plugins: [[VueQueryPlugin, { queryClient }], PrimeVue] } })
  return { wrapper, queryClient }
}

describe('system status', () => {
  it('shows live status and refreshes without enabling commands', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      service: 'szurubooru-toolkit', mode: 'scaffold', operations_enabled: false, static_ready: true,
    })))
    fetchMock.mockImplementation(async () => new Response(JSON.stringify({
      service: 'szurubooru-toolkit', mode: 'scaffold', operations_enabled: false, static_ready: true,
    })))
    vi.stubGlobal('fetch', fetchMock)
    const { wrapper, queryClient } = renderView()
    await vi.waitFor(() => expect(wrapper.text()).toContain('API connected'))
    expect(wrapper.text()).toContain('Ready')
    expect(wrapper.text()).toContain('Unavailable')
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    wrapper.unmount()
    queryClient.clear()
  })

  it('shows an error instead of claiming the API is online', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { wrapper, queryClient } = renderView()
    await vi.waitFor(() => expect(wrapper.text()).toContain('API connection unavailable'))
    expect(wrapper.text()).toContain('Unreachable')
    expect(wrapper.text()).not.toContain('Online')
    wrapper.unmount()
    queryClient.clear()
  })
})