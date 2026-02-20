import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import Charts from '@/pages/Charts.vue'
import Reports from '@/pages/Reports.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home,
    },
    {
        path: '/charts',
        name: 'Charts',
        component: Charts,
    },
    {
        path: '/reports',
        name: 'Reports',
        component: Reports,
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
