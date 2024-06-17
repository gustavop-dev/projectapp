import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/web-developments',
      name: 'webDevelopments',
      component: () => import("@/views/WebDevelopment/List.vue"),
    },
    {
      path: '/web-developments/detail/:development_id/:section_id/:component_id',
      name: 'webDevelopmentsDetail',
      component: () => import("@/views/WebDevelopment/Detail.vue"),
    },
    {
      path: '/web-designs',
      name: 'webDesigns',
      component: () => import("@/views/WebDesigns/List.vue"),
    },
    {
      path: '/3d-animations',
      name: '3dAnimations',
      component: () => import("@/views/3dAnimations/List.vue"),
    },
    {
      path: '/about-us',
      name: 'aboutUs',
      component: () => import("@/views/AboutUs.vue"),
    },
    {
      path: '/custom-software',
      name: 'customSoftware',
      component: () => import("@/views/CustomSoftware.vue"),
    },
    {
      path: '/e-commerce-prices',
      name: 'eCommercePrices',
      component: () => import("@/views/Prices.vue"),
    },
    {
      path: '/hosting',
      name: 'hosting',
      component: () => import("@/views/hosting.vue"),
    }
  ]
})

export default router
