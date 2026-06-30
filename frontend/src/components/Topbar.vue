<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isGuest = computed(() => !userStore.isLoggedIn)

function logout() {
  userStore.logout()
  router.push('/login')
}

function gotoLogin() {
  router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <router-link to="/library" class="logo">
        <span class="logo-icon">
          <svg viewBox="0 0 28 28" width="22" height="22" fill="none">
            <path d="M5 5h12.5v18.5H5z" fill="var(--color-primary)" opacity=".18" />
            <path d="M5 5h12.5v18.5H5z" stroke="var(--color-primary)" stroke-width="1.6" fill="none" />
            <path d="M17.5 5H23v18.5h-5.5" stroke="var(--color-primary)" stroke-width="1.6" fill="none" />
            <path d="M8 9h7M8 12.5h7M8 16h5" stroke="var(--color-primary)" stroke-width="1.2" stroke-linecap="round" opacity=".5" />
          </svg>
        </span>
        <span class="logo-text">
          <span class="logo-title">家庭图书馆</span>
          <span class="logo-sub">Family Library</span>
        </span>
      </router-link>

      <nav class="nav">
        <router-link to="/library" class="nav-item" :class="{ active: route.path === '/library' }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h4v16H3zM7 4h4v16H7zM11 4l4-1 5 17-4 1z" />
          </svg>
          <span>书架</span>
        </router-link>
        <router-link v-if="!isGuest" to="/records" class="nav-item" :class="{ active: route.path.startsWith('/records') }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 4h14M5 9h10M5 14h14M5 19h8" />
          </svg>
          <span>阅读记录</span>
        </router-link>
        <router-link v-if="!isGuest" to="/stats" class="nav-item" :class="{ active: route.path.startsWith('/stats') }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 20V10M10 20V4M16 20v-6M22 20H2" />
          </svg>
          <span>阅读统计</span>
        </router-link>
        <router-link v-if="!isGuest" to="/family" class="nav-item" :class="{ active: route.path.startsWith('/family') }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="8" r="3" />
            <circle cx="17" cy="9.5" r="2.2" />
            <path d="M3 19c0-3.3 2.7-6 6-6s6 2.7 6 6M14.5 19c0-2.2 1.7-4 4-4" />
          </svg>
          <span>家庭成员</span>
        </router-link>
        <router-link to="/about" class="nav-item" :class="{ active: route.path.startsWith('/about') }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 8h.01M11 12h1v5h1" />
          </svg>
          <span>关于</span>
        </router-link>
      </nav>

      <div class="topbar-right">
        <template v-if="!isGuest">
          <slot name="actions" />
          <div class="user-info">
            <span class="user-avatar">{{ (userStore.user?.nickname || '用').charAt(0) }}</span>
            <span class="user-name">{{ userStore.user?.nickname || '用户' }}</span>
            <button class="btn-link" @click="logout">退出</button>
          </div>
        </template>
        <template v-else>
          <button class="btn btn-primary btn-sm" @click="gotoLogin">登录</button>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(250, 247, 240, 0.92);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--color-border);
}
.topbar-inner {
  max-width: var(--content-max);
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: var(--space-6);
  height: var(--topbar-height);
  padding: 0 var(--space-6);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: inherit;
  flex-shrink: 0;
}
.logo-icon {
  width: 38px; height: 38px;
  background: var(--color-primary-tint);
  border: 1px solid var(--color-primary-soft);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  transition: transform var(--transition-normal);
}
.logo:hover .logo-icon { transform: rotate(-3deg); }
.logo-text {
  display: flex; flex-direction: column;
  line-height: 1.15;
}
.logo-title {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: 0.02em;
}
.logo-sub {
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.nav {
  display: flex;
  gap: 2px;
  margin-left: var(--space-4);
}
.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: 500;
  transition: all var(--transition-normal);
}
.nav-item:hover {
  color: var(--color-text-primary);
  background: var(--color-primary-tint);
}
.nav-item.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: -8px; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 16px;
  background: var(--color-primary);
  border-radius: 2px;
}

.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 4px 12px 4px 4px;
  background: var(--color-bg-paper-deep);
  border-radius: var(--radius-pill);
}
.user-avatar {
  width: 28px; height: 28px;
  background: var(--color-primary);
  color: var(--color-text-onPrimary);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-serif);
  font-weight: 600;
  font-size: var(--text-sm);
}
.user-name {
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  font-weight: 500;
}
.btn-link {
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  font-size: var(--text-xs);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.btn-link:hover { color: var(--color-danger); background: var(--color-danger-soft); }

@media (max-width: 768px) {
  .topbar-inner { gap: var(--space-3); padding: 0 var(--space-4); }
  .logo-text { display: none; }
  .nav { margin-left: 0; gap: 0; flex: 1; justify-content: flex-end; }
  .nav-item span { display: none; }
  .nav-item { padding: 8px 10px; }
  .user-name { display: none; }
}
</style>
