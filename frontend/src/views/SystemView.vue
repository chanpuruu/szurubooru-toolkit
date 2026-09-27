<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Check, CircleAlert, RefreshCw, Server, Shield, Package } from '@lucide/vue'
import Button from 'primevue/button'
import { getSystemStatus } from '../api'

const { data, isPending, isFetching, isError, dataUpdatedAt, refetch } = useQuery({
  queryKey: ['system-status'],
  queryFn: ({ signal }) => getSystemStatus(signal),
  retry: false,
  refetchInterval: 30_000,
})
const lastChecked = computed(() => dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : 'Not checked')
const apiState = computed(() => isPending.value ? 'Checking' : isError.value ? 'Unreachable' : 'Online')
</script>

<template>
  <section aria-labelledby="system-heading">
    <div class="page-heading">
      <div><p class="eyebrow">WORKSPACE STATUS</p><h1 id="system-heading">System</h1></div>
      <Button class="refresh-button" :disabled="isFetching" aria-label="Refresh status" @click="refetch()">
        <RefreshCw :size="16" :class="{ spinning: isFetching }" aria-hidden="true" />
        <span>Refresh</span>
      </Button>
    </div>
    <div class="status-banner" :class="{ degraded: isError }" role="status" aria-live="polite">
      <CircleAlert v-if="isError" :size="20" aria-hidden="true" />
      <Check v-else :size="20" aria-hidden="true" />
      <strong>{{ isPending ? 'Connecting to API' : isError ? 'API connection unavailable' : 'API connected' }}</strong>
      <span class="read-only-badge">Read only</span>
    </div>
    <div class="section-heading"><h2>Services</h2><span class="checked-at">Last response {{ lastChecked }}</span></div>
    <dl class="service-list" :aria-busy="isFetching">
      <div class="service-row">
        <dt><span class="service-icon"><Server :size="20" aria-hidden="true" /></span><span>Toolkit API<small>/api/v1/system/status</small></span></dt>
        <dd><span class="state-pill" :class="isError ? 'state-warning' : 'state-ok'">{{ apiState }}</span></dd>
      </div>
      <div class="service-row">
        <dt><span class="service-icon"><Package :size="20" aria-hidden="true" /></span><span>Frontend assets<small>Production bundle</small></span></dt>
        <dd><span class="state-pill" :class="data?.static_ready && !isError ? 'state-ok' : 'state-neutral'">{{ isError || !data ? 'Unknown' : data.static_ready ? 'Ready' : 'Not built' }}</span></dd>
      </div>
      <div class="service-row">
        <dt><span class="service-icon"><Shield :size="20" aria-hidden="true" /></span><span>Command execution<small>Operational access</small></span></dt>
        <dd><span class="state-pill state-neutral">{{ isError || !data ? 'Unknown' : 'Unavailable' }}</span></dd>
      </div>
    </dl>
    <div class="runtime-line"><span>Runtime</span><code>{{ isError || !data ? 'unknown' : data.mode }}</code></div>
  </section>
</template>