<script setup>
import Topbar from '../components/Topbar.vue'
import { ref, onMounted, computed } from 'vue'
import { bookApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const cacheStats = ref({ total: 0, hit_ok: 0, negative_cached: 0 })
const clearing = ref(false)
const isAdmin = computed(() => userStore.user?.role === 'admin')

async function loadCacheStats() {
  try {
    const r = await bookApi.metaCacheStats()
    cacheStats.value = r.data
  } catch (_) {}
}

async function clearCache() {
  if (!confirm(`确定清空所有 ${cacheStats.value.total} 条豆瓣元数据缓存吗?\n下次查 ISBN 会重新请求豆瓣。`)) return
  clearing.value = true
  try {
    await bookApi.clearMetaCache()
    await loadCacheStats()
  } catch (e) {
    alert(e.response?.data?.detail || '清空失败')
  } finally {
    clearing.value = false
  }
}

onMounted(loadCacheStats)
</script>

<template>
  <div class="page">
    <Topbar />
    <div class="page-body">
      <article class="about-card">
        <header class="about-head">
          <div class="brand-mark">
            <svg viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="var(--color-primary)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 5h13v22H5z" fill="var(--color-primary)" fill-opacity=".12"/>
              <path d="M18 5h9v22h-9z"/>
              <path d="M8 10h7M8 14h7M8 18h5M21 10h3M21 14h3"/>
            </svg>
          </div>
          <h1 class="about-title">关于家庭图书馆</h1>
          <p class="about-lede">
            一个简洁而温暖的家庭藏书管理工具, 帮助家人记录管理共同拥有的每一本书。
          </p>
        </header>

        <section class="about-section">
          <h2 class="section-title">核心功能</h2>
          <ul class="feature-list">
            <li>
              <span class="bullet"></span>
              <div>
                <strong>扫码/ISBN 一键添加</strong>
                <span>扫描或输入 13 位 ISBN, 自动从豆瓣拉取元数据</span>
              </div>
            </li>
            <li>
              <span class="bullet"></span>
              <div>
                <strong>智能缓存与降级</strong>
                <span>7 天本地缓存减少重复请求; 抓不到时自动切换到手动录入</span>
              </div>
            </li>
            <li>
              <span class="bullet"></span>
              <div>
                <strong>家庭成员共享</strong>
                <span>每位成员独立记录阅读进度, 每本书可归属到具体成员</span>
              </div>
            </li>
            <li>
              <span class="bullet"></span>
              <div>
                <strong>阅读数据统计</strong>
                <span>阅读时长、阅读次数、分类分布一目了然</span>
              </div>
            </li>
          </ul>
        </section>

        <section class="about-section">
          <h2 class="section-title">技术栈</h2>
          <ul class="stack-list">
            <li><span class="stack-label">前端</span> Vue 3 + Vite + Pinia</li>
            <li><span class="stack-label">后端</span> FastAPI + SQLAlchemy + SQLite</li>
            <li><span class="stack-label">部署</span> Docker + Docker Compose + Nginx</li>
            <li><span class="stack-label">数据源</span> 豆瓣 (HTML 爬虫 + 7 天本地缓存)</li>
          </ul>
        </section>

        <section class="about-section">
          <h2 class="section-title">使用提示</h2>
          <ul class="hint-list">
            <li>
              首次部署默认管理员 <code>admin</code> / <code>admin123</code>, 请尽快修改。
            </li>
            <li>
              豆瓣元数据 7 天本地缓存, 同一 ISBN 不会重复请求; 冷门书会显示"暂无评分", 可在详情页手动补评分、封面、简介。
            </li>
            <li>
              数据库文件位于 <code>data/library.db</code>, 升级前请备份。
            </li>
          </ul>
        </section>

        <section v-if="isAdmin" class="about-section">
          <h2 class="section-title">
            元数据缓存
            <button
              class="btn-mini"
              :disabled="clearing || cacheStats.total === 0"
              @click="clearCache"
            >
              {{ clearing ? '清理中...' : '清空缓存' }}
            </button>
          </h2>
          <div class="cache-stats">
            <div class="cache-cell">
              <span class="cache-num">{{ cacheStats.total }}</span>
              <span class="cache-lbl">总条目</span>
            </div>
            <div class="cache-cell">
              <span class="cache-num ok">{{ cacheStats.hit_ok }}</span>
              <span class="cache-lbl">成功缓存</span>
            </div>
            <div class="cache-cell">
              <span class="cache-num neg">{{ cacheStats.negative_cached }}</span>
              <span class="cache-lbl">已知无数据</span>
            </div>
          </div>
          <p class="cache-tip">
            缓存命中直接返回, 不打豆瓣; 失败/无数据也缓存 1 天, 避免冷门书反复打。
          </p>
        </section>
      </article>
    </div>
  </div>
</template>

<style scoped>
.page-body {
  max-width: var(--about-max);
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.about-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-10) var(--space-8);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  background-image:
    radial-gradient(circle at 0% 0%, rgba(139, 105, 20, 0.04) 0%, transparent 30%);
}
.about-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 4px;
  background: linear-gradient(90deg, var(--color-primary) 0%, #B8893A 50%, transparent 100%);
}

.about-head {
  text-align: center;
  padding-bottom: var(--space-6);
  margin-bottom: var(--space-8);
  border-bottom: 1px solid var(--color-border-soft);
}
.brand-mark {
  width: 64px; height: 64px;
  margin: 0 auto var(--space-4);
  background: var(--color-bg-paper-deep);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
}
.about-title {
  font-family: var(--font-serif);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-3);
  letter-spacing: 0.04em;
}
.about-lede {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.8;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}

.about-section { margin-bottom: var(--space-6); }
.about-section:last-child { margin-bottom: 0; }

.section-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-4);
  padding-left: var(--space-3);
  position: relative;
  display: flex; align-items: center;
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 18px;
  background: var(--color-primary);
  border-radius: 2px;
}

.feature-list,
.stack-list,
.hint-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.feature-list li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px dashed var(--color-border-soft);
}
.feature-list li:last-child { border-bottom: none; }
.feature-list .bullet {
  width: 6px; height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
}
.feature-list li > div { display: flex; flex-direction: column; }
.feature-list strong {
  font-family: var(--font-serif);
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: var(--text-base);
}
.feature-list span {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-top: 2px;
  line-height: 1.6;
}

.stack-list li {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) 0;
  font-size: var(--text-sm);
  color: var(--color-text-primary);
}
.stack-label {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 56px;
  padding: 3px 10px;
  background: var(--color-primary-tint);
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  font-family: var(--font-serif);
  font-weight: 600;
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
}

.hint-list li {
  position: relative;
  padding: var(--space-2) 0 var(--space-2) var(--space-5);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  line-height: 1.8;
}
.hint-list li::before {
  content: '·';
  position: absolute;
  left: var(--space-3);
  top: var(--space-2);
  color: var(--color-primary);
  font-size: var(--text-lg);
  font-weight: 700;
}

code {
  background: var(--color-bg-paper-deep);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  font-size: 0.9em;
  color: var(--color-primary);
  border: 1px solid var(--color-border);
}

/* 缓存 */
.btn-mini {
  margin-left: var(--space-3);
  font-size: var(--text-xs);
  padding: 4px 12px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  cursor: pointer;
  font-family: inherit;
  font-weight: 500;
  transition: all var(--transition-normal);
}
.btn-mini:hover:not(:disabled) {
  background: var(--color-danger);
  color: var(--color-bg-elevated);
}
.btn-mini:disabled { opacity: 0.4; cursor: not-allowed; }

.cache-stats {
  display: flex;
  gap: var(--space-3);
  margin: var(--space-3) 0;
  flex-wrap: wrap;
}
.cache-cell {
  flex: 1;
  min-width: 110px;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  text-align: center;
}
.cache-num {
  display: block;
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1;
}
.cache-num.ok { color: var(--color-success); }
.cache-num.neg { color: var(--color-warning); }
.cache-lbl {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-top: var(--space-2);
  letter-spacing: 0.04em;
}
.cache-tip {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: var(--space-2) 0 0;
  font-style: italic;
}

@media (max-width: 768px) {
  .page-body { padding: var(--space-5) var(--space-4); }
  .about-card { padding: var(--space-6) var(--space-5); }
  .about-title { font-size: var(--text-2xl); }
  .section-title { font-size: var(--text-lg); }
}
</style>
