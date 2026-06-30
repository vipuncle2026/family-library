<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { householdApi } from '../api'
import Topbar from '../components/Topbar.vue'

const userStore = useUserStore()
const household = ref(null)
const availableUsers = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editingMember = ref(null)
const errMsg = ref('')

const newMember = ref({
  display_name: '',
  relation: '成员',
  avatar_color: '#8B6914',
  user_id: null,
})

// 暖色调色板
const colorPalette = [
  '#8B6914', // 古铜金（主）
  '#A03828', // 朱红棕
  '#4A7C3F', // 森林绿
  '#4A6B7C', // 墨蓝
  '#B8740A', // 琥珀棕
  '#6B4F12', // 深古铜
  '#8B5A3C', // 红铜
  '#5C7A6F', // 竹青
]
const relations = ['自己', '配偶', '子女', '父母', '兄弟姐妹', '成员']

const isAdmin = computed(() => userStore.user?.role === 'admin')

const stats = computed(() => {
  if (!household.value?.members) return { total: 0, bound: 0 }
  const m = household.value.members
  return { total: m.length, bound: m.filter(x => x.user_id).length }
})

async function loadAll() {
  loading.value = true
  errMsg.value = ''
  try {
    const [h, u] = await Promise.all([
      householdApi.my(),
      isAdmin.value ? householdApi.availableUsers().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
    ])
    household.value = h.data
    availableUsers.value = u.data
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingMember.value = null
  newMember.value = {
    display_name: '',
    relation: '成员',
    avatar_color: colorPalette[Math.floor(Math.random() * colorPalette.length)],
    user_id: null,
  }
  showAddDialog.value = true
}

function openEdit(m) {
  editingMember.value = m
  newMember.value = {
    display_name: m.display_name,
    relation: m.relation,
    avatar_color: m.avatar_color,
    user_id: m.user_id,
  }
  showAddDialog.value = true
}

async function saveMember() {
  if (!newMember.value.display_name) {
    errMsg.value = '请输入成员名称'
    return
  }
  try {
    if (editingMember.value) {
      await householdApi.updateMember(editingMember.value.id, newMember.value)
    } else {
      await householdApi.addMember(newMember.value)
    }
    showAddDialog.value = false
    await loadAll()
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '保存失败'
  }
}

async function deleteMember(m) {
  if (!confirm(`确定要移除「${m.display_name}」吗？TA 的书会变成「未归属」`)) return
  try {
    await householdApi.removeMember(m.id)
    await loadAll()
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '删除失败'
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="page">
    <Topbar />
    <div class="page-body">
      <header class="page-head">
        <div>
          <h1 class="page-title">{{ household?.name || '我的家' }}</h1>
          <p class="page-hint">
            <span class="dot"></span>
            家庭成员 · 每本书可以归属到具体成员，记录阅读进度
          </p>
        </div>
        <button v-if="isAdmin" class="btn btn-primary" @click="openAdd">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          添加成员
        </button>
      </header>

      <div v-if="errMsg" class="err">{{ errMsg }}</div>

      <!-- 统计 -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ stats.total }}</span>
          <span class="stat-label">家庭成员</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.bound }}</span>
          <span class="stat-label">已绑定账号</span>
        </div>
      </div>

      <!-- 成员列表 -->
      <div v-if="loading" class="loading">
        <span class="spinner"></span>
        <span>正在清点家庭成员...</span>
      </div>
      <div v-else-if="household?.members?.length" class="members">
        <div v-for="m in household.members" :key="m.id" class="member-card">
          <div class="avatar" :style="{ background: m.avatar_color }">
            <span>{{ m.display_name?.[0] || '?' }}</span>
          </div>
          <div class="info">
            <div class="member-head">
              <h3 class="member-name">{{ m.display_name }}</h3>
              <span class="relation">{{ m.relation }}</span>
            </div>
            <p class="m-meta">
              <span v-if="m.bound_username" class="bound">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                已绑定 @{{ m.bound_username }}
              </span>
              <span v-else class="unbound">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <circle cx="12" cy="12" r="9"/>
                  <path d="M9 9l6 6M15 9l-6 6"/>
                </svg>
                未绑定账号
              </span>
            </p>
          </div>
          <div v-if="isAdmin" class="actions">
            <button class="icon-btn" @click="openEdit(m)" title="编辑">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4v16h16v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="icon-btn danger" @click="deleteMember(m)" title="移除">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty">
        <div class="empty-illu">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none">
            <circle cx="28" cy="28" r="10" fill="var(--color-primary)" fill-opacity=".12" stroke="var(--color-primary)" stroke-width="1.4"/>
            <circle cx="52" cy="28" r="10" fill="var(--color-primary)" fill-opacity=".10" stroke="var(--color-primary)" stroke-width="1.4" opacity=".7"/>
            <path d="M14 60c0-8 6-14 14-14s14 6 14 14" fill="var(--color-primary)" fill-opacity=".12" stroke="var(--color-primary)" stroke-width="1.4"/>
            <path d="M38 60c0-8 6-14 14-14s14 6 14 14" fill="var(--color-primary)" fill-opacity=".10" stroke="var(--color-primary)" stroke-width="1.4" opacity=".7"/>
          </svg>
        </div>
        <p class="empty-title">还没有家庭成员</p>
        <p class="empty-sub">点击「添加成员」，建立家庭档案</p>
      </div>

      <!-- 添加/编辑弹窗 -->
      <div v-if="showAddDialog" class="overlay" @click.self="showAddDialog = false">
        <div class="modal">
          <div class="modal-head">
            <h2 class="modal-title">{{ editingMember ? '编辑成员' : '添加成员' }}</h2>
            <p class="modal-sub">{{ editingMember ? '更新家庭成员信息' : '为家庭添加新成员' }}</p>
          </div>

          <div class="field">
            <label class="field-label">名称 <span class="req">*</span></label>
            <input v-model="newMember.display_name" class="input" placeholder="例：女儿 / 夫人" />
          </div>

          <div class="field">
            <label class="field-label">关系</label>
            <select v-model="newMember.relation" class="input">
              <option v-for="r in relations" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>

          <div class="field">
            <label class="field-label">头像颜色</label>
            <div class="color-row">
              <button
                v-for="c in colorPalette"
                :key="c"
                type="button"
                class="color-dot"
                :class="{ active: newMember.avatar_color === c }"
                :style="{ background: c }"
                @click="newMember.avatar_color = c"
                :aria-label="c"
              ></button>
            </div>
          </div>

          <div class="field">
            <label class="field-label">绑定账号 <span class="muted">（可选）</span></label>
            <select v-model="newMember.user_id" class="input">
              <option :value="null">暂不绑定</option>
              <option
                v-for="u in availableUsers.filter(x => !x.is_bound || x.id === newMember.user_id)"
                :key="u.id"
                :value="u.id"
              >
                {{ u.nickname }} (@{{ u.username }}){{ u.role === 'admin' ? ' · 管理员' : '' }}
              </option>
            </select>
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showAddDialog = false">取消</button>
            <button class="btn btn-primary" @click="saveMember">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-body {
  max-width: 880px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.page-head {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: var(--space-6);
  gap: var(--space-4);
  flex-wrap: wrap;
}
.page-title {
  font-family: var(--font-serif);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
  letter-spacing: 0.04em;
}
.page-hint {
  display: inline-flex; align-items: center; gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  margin: 0;
}
.page-hint .dot {
  width: 5px; height: 5px;
  background: var(--color-primary);
  border-radius: 50%;
}

.err {
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
  border-left: 3px solid var(--color-danger);
}

/* === 统计 === */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.stat-card {
  background: var(--color-bg-paper-deep);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  text-align: center;
  position: relative;
  overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute;
  top: -20px; right: -20px;
  width: 80px; height: 80px;
  background: var(--color-primary);
  opacity: 0.04;
  border-radius: 50%;
}
.stat-num {
  display: block;
  font-family: var(--font-serif);
  font-size: var(--text-4xl);
  font-weight: 600;
  color: var(--color-primary);
  line-height: 1;
  letter-spacing: -0.02em;
}
.stat-label {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-2);
  letter-spacing: 0.04em;
}

/* === 成员 === */
.members { display: flex; flex-direction: column; gap: var(--space-3); }
.member-card {
  display: flex; align-items: center; gap: var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-soft);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}
.member-card:hover {
  border-color: var(--color-border);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.avatar {
  width: 56px; height: 56px;
  border-radius: 50%;
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.2);
}
.info { flex: 1; min-width: 0; }
.member-head { display: flex; align-items: center; gap: var(--space-2); margin-bottom: 4px; }
.member-name {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}
.relation {
  display: inline-flex; align-items: center;
  padding: 2px 10px;
  background: var(--color-primary-tint);
  color: var(--color-primary);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 500;
  font-family: var(--font-serif);
}
.m-meta {
  margin: 0;
  font-size: var(--text-sm);
  display: flex; align-items: center; gap: 4px;
}
.bound {
  display: inline-flex; align-items: center; gap: 4px;
  color: var(--color-success);
  font-weight: 500;
}
.unbound {
  display: inline-flex; align-items: center; gap: 4px;
  color: var(--color-text-tertiary);
}

.actions { display: flex; gap: var(--space-2); }
.icon-btn {
  width: 36px; height: 36px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-normal);
}
.icon-btn:hover {
  background: var(--color-primary-tint);
  color: var(--color-primary);
  border-color: var(--color-primary);
}
.icon-btn.danger:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.loading {
  display: flex; align-items: center; gap: var(--space-3);
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--color-text-secondary);
  font-family: var(--font-serif);
  font-style: italic;
}

.empty { text-align: center; padding: 80px 20px; }
.empty-illu { margin-bottom: var(--space-5); opacity: 0.7; }
.empty-title {
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
}
.empty-sub { color: var(--color-text-secondary); margin: 0; font-size: var(--text-sm); }

/* === 弹窗 === */
.modal {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  width: 90%; max-width: 440px;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
  animation: modalIn 0.25s ease;
}
.modal-head { margin-bottom: var(--space-5); }
.modal-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1);
}
.modal-sub { color: var(--color-text-secondary); margin: 0; font-size: var(--text-sm); }

.field { margin-bottom: var(--space-4); }
.req { color: var(--color-danger); }
.muted { color: var(--color-text-tertiary); font-weight: 400; font-size: var(--text-xs); }

.color-row { display: flex; gap: var(--space-2); flex-wrap: wrap; }
.color-dot {
  width: 32px; height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all var(--transition-normal);
  padding: 0;
  outline: none;
}
.color-dot:hover { transform: scale(1.1); }
.color-dot.active {
  border-color: var(--color-text-primary);
  box-shadow: 0 0 0 2px var(--color-bg-elevated) inset;
}

.modal-actions {
  display: flex; justify-content: flex-end; gap: var(--space-2);
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .page-body { padding: var(--space-5) var(--space-4); }
  .page-title { font-size: var(--text-2xl); }
  .stats-row { grid-template-columns: 1fr; }
  .member-card { padding: var(--space-3) var(--space-4); }
  .avatar { width: 48px; height: 48px; font-size: var(--text-lg); }
}
</style>
