<script setup lang="ts">
import { Activity, ArrowUpRight } from '@lucide/vue'
import toolkitMark from './assets/toolkit.png'
</script>

<template>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <img :src="toolkitMark" width="36" height="36" alt="" />
        <div><strong>szurubooru</strong><span>toolkit</span></div>
      </div>
      <nav aria-label="Main navigation">
        <RouterLink to="/system"><Activity :size="18" aria-hidden="true" /> System</RouterLink>
      </nav>
      <div class="sidebar-footer"><span class="status-dot" /> Development</div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <span>Workspace <span class="separator">/</span> System</span>
        <a href="https://github.com/reluce/szurubooru-toolkit" target="_blank" rel="noopener noreferrer">
          Repository <ArrowUpRight :size="15" aria-hidden="true" />
        </a>
      </header>
      <main id="main" tabindex="-1"><RouterView /></main>
      <footer class="workspace-footer"><span>szurubooru-toolkit</span><span>Web foundation</span></footer>
    </div>
  </div>
</template>
