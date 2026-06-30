<script setup>
import { ref, computed, onMounted } from 'vue'
import { readingApi, bookApi } from '../api'
import Topbar from '../components/Topbar.vue'

const stats = ref({ total_minutes: 0, record_count: 0, finished_books: 0, days: 30 })
const library = ref({ total: 0, categories: [], statuses: [] })
const loading = ref(false)

async function fetchAll() {
  loading.value = true
  try {
    const [a, b] = await Promise.all([readingApi.stats({ days: 30 }), bookApi.stats()])
    stats.value = a.data
    library.value = b.data
  } finally {
    loading.value = false
  }
}

const hours = computed(() => (stats.value.total_minutes / 60).toFixed(1))
const statusLabel = (s) => ({ unread: '未开始', reading: '在读中', finished: '已读完' }[s] || s)
const statusConfig = {
  unread:   { color: 'var(--color-text-tertiary)',  bg: 'var(--color-bg-sunken)' },
  reading:  { color: 'var(--color-reading)',        bg: 'var(--color-warning-soft)' },
  finished: { color: 'var(--color-success)',        bg: 'var(--color-success-soft)' },
}

// 分类最大占比
const maxCategoryCount = computed(() => {
  if (!library.value.categories?.length) return 1
  return Math.max(...library.value.categories.map(c => c.count))
})

// 每日平均
const avgMinutesPerDay = computed(() => {
  if (!stats.value.days) return 0
  return Math.round(stats.value.total_minutes / stats.value.days)
})

onMounted(fetchAll)
</script>

<template>
  <div class="page">
    <Topbar />
    <div class="page-body">
      <header class="page-head">
        <h1 class="page-title">阅读统计</h1>
        <p class="page-hint">
          <span class="dot"></span>
          最近 <strong>{{ stats.days }}</strong> 天的阅读轨迹
        </p>
      </header>

      <div v-if="loading" class="loading">
        <span class="spinner"></span>
        <span>正在汇总数据...</span>
      </div>

      <template v-else>
        <!-- KPI 卡 -->
        <section class="kpi-grid">
          <div class="kpi-card kpi-featured">
            <div class="kpi-label">总阅读时长</div>
            <div class="kpi-value-wrap">
              <span class="kpi-value">{{ hours }}</span>
              <span class="kpi-unit">小时</span>
            </div>
            <div class="kpi-foot">
              <span>日均 <strong>{{ avgMinutesPerDay }}</strong> 分钟</span>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">阅读次数</div>
            <div class="kpi-value-wrap">
              <span class="kpi-value">{{ stats.record_count }}</span>
              <span class="kpi-unit">次</span>
            </div>
            <div class="kpi-foot">
              <span>30 天内记录</span>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">读完的书</div>
            <div class="kpi-value-wrap">
              <span class="kpi-value">{{ stats.finished_books }}</span>
              <span class="kpi-unit">本</span>
            </div>
            <div class="kpi-foot">
              <span>30 天内完读</span>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">总藏书</div>
            <div class="kpi-value-wrap">
              <span class="kpi-value">{{ library.total }}</span>
              <span class="kpi-unit">本</span>
            </div>
            <div class="kpi-foot">
              <span>家庭书架容量</span>
            </div>
          </div>
        </section>

        <!-- 分类分布 -->
        <section class="section">
          <h2 class="section-title">分类分布</h2>
          <p class="section-hint">书架上的藏书类别构成</p>

          <div v-if="!library.categories?.length" class="empty-section">暂无分类数据</div>
          <div v-else class="cat-list">
            <div v-for="(c, i) in library.categories" :key="c.name" class="cat-row">
              <span class="cat-rank">{{ i + 1 }}</span>
              <span class="cat-name">{{ c.name }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (c.count / maxCategoryCount * 100) + '%' }"></div>
              </div>
              <span class="cat-count">{{ c.count }}</span>
            </div>
          </div>
        </section>

        <!-- 阅读状态 -->
        <section class="section">
          <h2 class="section-title">阅读状态</h2>
          <p class="section-hint">当前各状态书的分布</p>

          <div v-if="!library.statuses?.length" class="empty-section">暂无状态数据</div>
          <div v-else class="status-list">
            <div
              v-for="s in library.statuses"
              :key="s.name"
              class="status-chip"
              :style="{
                background: statusConfig[s.name]?.bg,
                color: statusConfig[s.name]?.color,
              }"
            >
              <span class="dot" :style="{ background: statusConfig[s.name]?.color }"></span>
              <span class="status-name">{{ statusLabel(s.name) }}</span>
              <span class="cnt">{{ s.count }}</span>
            </div>
          </div>
        </section>
      </template>
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
  font-size: var(--text-md);
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

/* === KPI === */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}
.kpi-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-normal);
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}
.kpi-card.kpi-featured {
  background: linear-gradient(135deg, var(--color-bg-paper-deep) 0%, var(--color-bg-elevated) 100%);
  border-color: var(--color-primary-soft);
}
.kpi-card.kpi-featured::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  background: var(--color-primary);
}

.kpi-label {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
  margin-bottom: var(--space-3);
  letter-spacing: 0.04em;
}
.kpi-value-wrap {
  display: flex; align-items: baseline; gap: var(--space-2);
  margin-bottom: var(--space-3);
}
.kpi-value {
  font-family: var(--font-serif);
  font-size: var(--text-4xl);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1;
  letter-spacing: -0.01em;
}
.kpi-card.kpi-featured .kpi-value { color: var(--color-primary); }
.kpi-unit {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  color: var(--color-text-tertiary);
  font-weight: 500;
}
.kpi-foot {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-soft);
}
.kpi-foot strong { color: var(--color-text-primary); font-weight: 600; }

/* === Section === */
.section {
  margin-bottom: var(--space-8);
  padding: var(--space-6);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.section-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1);
  position: relative;
  padding-left: var(--space-3);
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 16px;
  background: var(--color-primary);
  border-radius: 2px;
}
.section-hint {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-5);
  padding-left: var(--space-3);
}
.empty-section {
  text-align: center;
  color: var(--color-text-tertiary);
  padding: var(--space-6) 0;
  font-family: var(--font-serif);
  font-style: italic;
}

/* === 分类 === */
.cat-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.cat-row {
  display: grid;
  grid-template-columns: 24px 80px 1fr 50px;
  align-items: center;
  gap: var(--space-3);
}
.cat-rank {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  text-align: center;
  font-weight: 500;
}
.cat-row:nth-child(1) .cat-rank,
.cat-row:nth-child(2) .cat-rank,
.cat-row:nth-child(3) .cat-rank {
  color: var(--color-primary);
  font-weight: 600;
}
.cat-name {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  font-weight: 500;
}
.bar-track {
  background: var(--color-bg-sunken);
  height: 8px;
  border-radius: var(--radius-pill);
  overflow: hidden;
  position: relative;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, #B8893A 100%);
  border-radius: var(--radius-pill);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(139, 105, 20, 0.2);
}
.cat-count {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  font-weight: 600;
  text-align: right;
}

/* === 状态 === */
.status-list {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.status-chip {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
  font-family: var(--font-serif);
  transition: all var(--transition-normal);
  border: 1px solid currentColor;
  border-color: transparent;
}
.status-chip:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
.status-chip .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-chip .status-name { font-weight: 500; }
.status-chip .cnt {
  font-weight: 700;
  margin-left: var(--space-2);
  padding-left: var(--space-2);
  border-left: 1px solid currentColor;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .page-body { padding: var(--space-5) var(--space-4); }
  .page-title { font-size: var(--text-2xl); }
  .kpi-grid { grid-template-columns: 1fr; }
  .cat-row { grid-template-columns: 24px 60px 1fr 40px; }
  .kpi-value { font-size: var(--text-3xl); }
}
</style>
