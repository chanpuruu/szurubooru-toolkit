import { createRouter, createWebHistory } from 'vue-router'
import SystemView from './views/SystemView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/system' },
    { path: '/system', component: SystemView },
  ],
})