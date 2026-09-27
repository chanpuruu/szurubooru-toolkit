import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import '@fontsource-variable/public-sans'
import '@fontsource/ibm-plex-mono/400.css'
import './shell.css'
import App from './App.vue'
import { router } from './router'

createApp(App)
	.use(router)
	.use(VueQueryPlugin)
	.use(PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: false } } })
	.mount('#app')
