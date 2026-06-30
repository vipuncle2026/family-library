import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
    { path: '/library', name: 'library', component: () => import('../views/Library.vue'), meta: { auth: false } },
    { path: '/records', name: 'records', component: () => import('../views/Records.vue'), meta: { auth: true } },
    { path: '/stats', name: 'stats', component: () => import('../views/Stats.vue'), meta: { auth: true } },
    { path: '/family', name: 'family', component: () => import('../views/Family.vue'), meta: { auth: true } },
    { path: '/about', name: 'about', component: () => import('../views/About.vue') },
  ],
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.auth && !userStore.isLoggedIn) {
    return next('/login')
  }
  next()
})

export default router
