<script setup>
import { ref, onMounted, computed } from 'vue'
import { readingApi, bookApi } from '../api'
import Topbar from '../components/Topbar.vue'

const records = ref([])
const loading = ref(false)
const bookMap = ref({})

async function fetchRecords() {
  loading.value = true
  try {
    const r = await readingApi.records({ limit: 100 })
    records.value = r.data
    const ids = [...new Set(r.data.map(x => x.book_id))]
    await Promise.all(ids.map(async (id) => {
      if (!bookMap.value[id]) {
        try {
          const b = await bookApi.detail(id)
          bookMap.value = { ...bookMap.value, [id]: b.data }
        } catch (_) {}
      }
    }))
  } finally {
    loading.value = false
  }
}

function fmtDate(d) {
  const date = new Date(d)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 3) return `${Math.floor(diff / 86400)} 天前`
  return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
}

function fmtTime(d) {
  return new Date(d).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

const totalMinutes = computed(() => records.value.reduce((s, r) => s + (r.duration_minutes || 0), 0))
const totalHours = computed(() => (totalMinutes.value / 60).toFixed(1))

onMounted(fetchRecords)
</script>

<template>
  <div class="page">
    <Topbar />
    <div class="page-body">
      <header class="page-head">
        <h1 class="page-title">阅读记录</h1>
        <p class="page-hint">
          <span class="dot"></span>
          最近 <strong>{{ records.length }}</strong> 条 · 累计 <strong>{{ totalHours }}</strong> 小时
        </p>
      </header>

      <div v-if="loading" class="loading">
        <span class="spinner"></span>
        <span>正在翻阅记录...</span>
      </div>

      <div v-else-if="!records.length" class="empty">
        <div class="empty-illu">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none">
            <path d="M20 12h32a4 4 0 0 1 4 4v48a0 0 0 0 1 0 0H16a0 0 0 0 1 0 0V16a4 4 0 0 1 4-4z" fill="var(--color-primary)" fill-opacity=".10" stroke="var(--color-primary)" stroke-width="1.4"/>
            <path d="M24 24h24M24 32h24M24 40h16" stroke="var(--color-primary)" stroke-width="1.4" stroke-linecap="round" opacity=".6"/>
            <circle cx="56" cy="60" r="12" fill="var(--color-bg-elevated)" stroke="var(--color-primary)" stroke-width="1.4"/>
            <path d="M60 60l4 4" stroke="var(--color-primary)" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="empty-title">还没有阅读记录</p>
        <p class="empty-sub">去书架选一本书, 翻开第一页吧</p>
      </div>

      <div v-else class="record-list">
        <article v-for="r in records" :key="r.id" class="record-card">
          <div class="cover-mini">
            <img
              v-if="bookMap[r.book_id]?.cover_url"
              :src="bookMap[r.book_id].cover_url"
              :alt="bookMap[r.book_id]?.title"
              referrerpolicy="no-referrer"
            />
            <div v-else class="cover-fb">
              <span>{{ (bookMap[r.book_id]?.title || '?').slice(0, 2) }}</span>
            </div>
          </div>

          <div class="rec-body">
            <div class="rec-head">
              <h3 class="rec-title">{{ bookMap[r.book_id]?.title || `书 #${r.book_id}` }}</h3>
              <span class="rec-time">{{ fmtDate(r.read_at) }}<span class="rec-time-dot">·</span>{{ fmtTime(r.read_at) }}</span>
            </div>

            <div class="meta-row">
              <span v-if="r.progress" class="badge progress">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                  <path d="M3 12a9 9 0 0 1 9-9 9 9 0 0 1 6.4 2.6L21 8"/>
                  <path d="M21 3v5h-5"/>
                </svg>
                {{ r.progress }}%
              </span>
              <span v-if="r.current_page" class="badge">第 {{ r.current_page }} 页</span>
              <span v-if="r.duration_minutes" class="badge badge-accent">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <circle cx="12" cy="12" r="9"/>
                  <path d="M12 7v5l3 2"/>
                </svg>
                {{ r.duration_minutes }} 分钟
              </span>
            </div>

            <!-- 进度条 -->
            <div v-if="r.progress" class="progress-bar">
              <div class="progress-fill" :style="{ width: r.progress + '%' }"></div>
            </div>

            <p v-if="r.note" class="note">
              <span class="note-quote">"</span>{{ r.note }}<span class="note-quote close">"</span>
            </p>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-body {
  max-width: var(--reading-max);
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.page-head { margin-bottom: var(--space-8); }
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
.page-hint strong {
  color: var(--color-primary);
  font-family: var(--font-serif);
  font-weight: 600;
}
.page-hint .dot {
  width: 5px; height: 5px;
  background: var(--color-primary);
  border-radius: 50%;
}

.loading {
  display: flex; align-items: center; gap: var(--space-3);
  justify-content: center;
  padding: 100px 0;
  color: var(--color-text-secondary);
  font-family: var(--font-serif);
  font-style: italic;
}

.empty { text-align: center; padding: 100px 20px; }
.empty-illu { margin-bottom: var(--space-5); opacity: 0.7; }
.empty-title {
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
}
.empty-sub {
  color: var(--color-text-secondary);
  margin: 0;
  font-size: var(--text-sm);
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.record-card {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
  position: relative;
}
.record-card:hover {
  border-color: var(--color-border);
  box-shadow: var(--shadow-md);
  transform: translateX(2px);
}
.record-card::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 0;
  background: var(--color-primary);
  border-radius: 2px;
  transition: height var(--transition-normal);
}
.record-card:hover::before { height: 60%; }

.cover-mini {
  flex-shrink: 0;
  width: 64px; height: 90px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.cover-mini img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}
.cover-fb {
  width: 100%; height: 100%;
  background: var(--color-bg-paper-deep);
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 11px,
      rgba(139, 105, 20, 0.05) 11px,
      rgba(139, 105, 20, 0.05) 12px
    );
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-serif);
  font-size: var(--text-md);
  color: var(--color-primary);
  font-weight: 600;
}

.rec-body { flex: 1; min-width: 0; }
.rec-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}
.rec-title {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rec-time {
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  font-family: var(--font-serif);
  font-style: italic;
}
.rec-time-dot { margin: 0 4px; }

.meta-row {
  display: flex; align-items: center; gap: var(--space-2);
  flex-wrap: wrap;
  margin-bottom: var(--space-2);
}
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px;
  background: var(--color-bg-sunken);
  color: var(--color-text-secondary);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 500;
}
.badge.progress {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}
.badge.badge-accent {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.progress-bar {
  height: 4px;
  background: var(--color-bg-sunken);
  border-radius: var(--radius-pill);
  overflow: hidden;
  margin-bottom: var(--space-2);
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, #B8893A 100%);
  border-radius: var(--radius-pill);
  transition: width 0.4s ease;
}

.note {
  margin: var(--space-2) 0 0;
  padding: var(--space-2) var(--space-3);
  background: var(--color-primary-tint);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  line-height: 1.7;
  font-family: var(--font-serif);
  font-style: italic;
}
.note-quote { color: var(--color-primary); font-size: var(--text-md); font-weight: 600; }
.note-quote.close { margin-left: 2px; }

@media (max-width: 768px) {
  .page-body { padding: var(--space-5) var(--space-4); }
  .page-title { font-size: var(--text-2xl); }
  .record-card { padding: var(--space-3) var(--space-4); gap: var(--space-3); }
  .cover-mini { width: 52px; height: 72px; }
  .rec-time { display: none; }
}
</style>
