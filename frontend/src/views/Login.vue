<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errMsg = ref('')
const isRegister = ref(false)
const nickname = ref('')

async function handleSubmit() {
  if (!username.value || !password.value) {
    errMsg.value = '请填写完整'
    return
  }
  if (isRegister.value && !nickname.value) {
    errMsg.value = '请填写昵称'
    return
  }
  errMsg.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await userStore.register({
        username: username.value,
        nickname: nickname.value,
        password: password.value,
      })
    } else {
      await userStore.login({ username: username.value, password: password.value })
    }
    router.push('/library')
  } catch (e) {
    errMsg.value = e.response?.data?.detail || (isRegister.value ? '注册失败' : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="bookshelf-deco" aria-hidden="true">
      <div class="book book-1"></div>
      <div class="book book-2"></div>
      <div class="book book-3"></div>
      <div class="book book-4"></div>
      <div class="book book-5"></div>
      <div class="book book-6"></div>
      <div class="book book-7"></div>
      <div class="book book-8"></div>
    </div>

    <div class="login-container">
      <!-- 左侧品牌区 -->
      <section class="brand-pane">
        <div class="brand-mark">
          <svg viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="var(--color-primary)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 5h13v22H5z" fill="var(--color-primary)" fill-opacity=".12" />
            <path d="M18 5h9v22h-9z" />
            <path d="M8 10h7M8 14h7M8 18h5M21 10h3M21 14h3" />
          </svg>
        </div>

        <h1 class="brand-headline">家的书房</h1>
        <p class="brand-subline">A Library Belongs to Family</p>

        <p class="brand-desc">
          在这里，每一本书都是家人的记忆。<br />
          记录阅读、分享所读、传承所爱。
        </p>

        <div class="brand-list">
          <div class="brand-item">
            <span class="dot"></span>
            <div>
              <strong>扫码录入</strong>
              <span>ISBN 自动获取豆瓣元数据</span>
            </div>
          </div>
          <div class="brand-item">
            <span class="dot"></span>
            <div>
              <strong>家庭共享</strong>
              <span>成员协作、归属追踪</span>
            </div>
          </div>
          <div class="brand-item">
            <span class="dot"></span>
            <div>
              <strong>阅读数据</strong>
              <span>进度、时长、习惯分析</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧表单区 -->
      <section class="form-pane">
        <div class="form-header">
          <h2 class="form-title">{{ isRegister ? '创建账户' : '欢迎回来' }}</h2>
          <p class="form-subtitle">{{ isRegister ? '加入家庭图书馆' : '登录继续阅读' }}</p>
        </div>

        <div class="tabs">
          <button
            type="button"
            :class="['tab', { active: !isRegister }]"
            @click="isRegister = false; errMsg = ''"
          >登录</button>
          <button
            type="button"
            :class="['tab', { active: isRegister }]"
            @click="isRegister = true; errMsg = ''"
          >注册</button>
        </div>

        <form v-if="!isRegister" @submit.prevent="handleSubmit" class="form">
          <div class="field">
            <label class="field-label" for="login-username">用户名 / 昵称</label>
            <input id="login-username" v-model="username" class="input" placeholder="请输入用户名或昵称" autocomplete="username" />
          </div>
          <div class="field">
            <label class="field-label" for="login-password">密码</label>
            <input id="login-password" v-model="password" type="password" class="input" placeholder="请输入密码" autocomplete="current-password" />
          </div>
          <div v-if="errMsg" class="err">{{ errMsg }}</div>
          <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else>登 录</span>
          </button>
          <p class="form-tip">
            首次使用？<a @click="isRegister = true">创建账户</a>
            <span class="divider-dot">·</span>
            <a @click="$router.push('/library')">先逛逛</a>
          </p>
        </form>

        <form v-else @submit.prevent="handleSubmit" class="form">
          <div class="field">
            <label class="field-label" for="reg-username">用户名</label>
            <input id="reg-username" v-model="username" class="input" placeholder="3-50字符, 字母数字" autocomplete="username" />
          </div>
          <div class="field">
            <label class="field-label" for="reg-nickname">昵称</label>
            <input id="reg-nickname" v-model="nickname" class="input" placeholder="显示用昵称" />
          </div>
          <div class="field">
            <label class="field-label" for="reg-password">密码</label>
            <input id="reg-password" v-model="password" type="password" class="input" placeholder="至少6位" autocomplete="new-password" />
          </div>
          <div v-if="errMsg" class="err">{{ errMsg }}</div>
          <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else>注 册</span>
          </button>
          <p class="form-tip">
            已有账户？<a @click="isRegister = false">返回登录</a>
          </p>
        </form>

        <p class="guest-tip">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 8h.01M11 12h1v5h1" />
          </svg>
          <span>游客可浏览书架，登录后使用更多功能</span>
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  background-image:
    radial-gradient(circle at 20% 0%, rgba(139, 105, 20, 0.04) 0%, transparent 40%),
    radial-gradient(circle at 80% 100%, rgba(139, 105, 20, 0.06) 0%, transparent 50%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  position: relative;
  overflow: hidden;
}

/* === 装饰：书架上的书 === */
.bookshelf-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.5;
}
.book {
  position: absolute;
  width: 16px;
  background: var(--color-primary);
  border-radius: 2px 2px 0 0;
  opacity: 0.07;
}
.book-1 { left: 4%;  top: 18%; height: 80px; transform: rotate(-3deg); }
.book-2 { left: 5%;  top: 22%; height: 60px; transform: rotate(2deg); background: var(--color-info); }
.book-3 { left: 7%;  top: 14%; height: 100px; transform: rotate(-1deg); }
.book-4 { left: 3%;  top: 28%; height: 50px; transform: rotate(1deg); background: var(--color-success); }
.book-5 { right: 4%; top: 24%; height: 90px; transform: rotate(2deg); }
.book-6 { right: 6%; top: 18%; height: 70px; transform: rotate(-2deg); background: var(--color-warning); }
.book-7 { right: 3%; top: 32%; height: 55px; transform: rotate(1deg); }
.book-8 { right: 8%; top: 14%; height: 110px; transform: rotate(-1deg); background: var(--color-danger); }

.login-container {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  width: 100%;
  max-width: 960px;
  min-height: 580px;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
}

/* === 左侧品牌区 === */
.brand-pane {
  position: relative;
  background: var(--color-bg-paper-deep);
  padding: 56px 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-right: 1px solid var(--color-border);
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 3px,
      rgba(139, 105, 20, 0.025) 3px,
      rgba(139, 105, 20, 0.025) 4px
    );
}
.brand-mark {
  width: 56px; height: 56px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: var(--space-8);
}
.brand-headline {
  font-family: var(--font-serif);
  font-size: var(--text-4xl);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.15;
  letter-spacing: 0.04em;
  margin: 0;
}
.brand-subline {
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--color-text-tertiary);
  font-size: var(--text-md);
  margin: var(--space-2) 0 var(--space-8);
  letter-spacing: 0.06em;
}
.brand-desc {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  color: var(--color-text-secondary);
  line-height: 1.9;
  margin: 0 0 var(--space-8);
}
.brand-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.brand-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}
.brand-item .dot {
  width: 6px; height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
}
.brand-item div {
  display: flex; flex-direction: column;
  font-size: var(--text-sm);
}
.brand-item strong {
  color: var(--color-text-primary);
  font-weight: 600;
  font-family: var(--font-serif);
}
.brand-item span {
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* === 右侧表单区 === */
.form-pane {
  padding: 56px 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-header { margin-bottom: var(--space-6); }
.form-title {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: 0.02em;
}
.form-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: var(--space-2) 0 0;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--color-bg-sunken);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
  width: 100%;
  max-width: 320px;
}
.tab {
  flex: 1;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: var(--text-sm);
  transition: all var(--transition-normal);
  font-family: inherit;
}
.tab.active {
  background: var(--color-bg-elevated);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.form { width: 100%; max-width: 320px; }
.field { margin-bottom: var(--space-4); }
.err {
  padding: 10px 12px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-3);
  border-left: 3px solid var(--color-danger);
}
.form-tip {
  text-align: center;
  margin: var(--space-4) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}
.form-tip a {
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 500;
  transition: color var(--transition-fast);
}
.form-tip a:hover { color: var(--color-primary-hover); text-decoration: underline; }
.divider-dot { margin: 0 var(--space-2); color: var(--color-text-tertiary); }

.guest-tip {
  display: flex; align-items: center; gap: var(--space-2);
  margin-top: var(--space-6);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-sunken);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  width: 100%; max-width: 320px;
}

@media (max-width: 768px) {
  .login-container { grid-template-columns: 1fr; min-height: auto; }
  .brand-pane { display: none; }
  .form-pane { padding: 40px 24px; }
}
</style>
