<script setup>
import { ref, onMounted, computed } from 'vue'
import { bookApi } from '../api'
import { useUserStore } from '../stores/user'
import BookDetail from '../components/BookDetail.vue'
import AddBookDialog from '../components/AddBookDialog.vue'
import Topbar from '../components/Topbar.vue'

const userStore = useUserStore()

const books = ref([])
const stats = ref({ total: 0, categories: [], statuses: [] })
const categories = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const activeCategory = ref('全部')
const selectedBook = ref(null)
const showAddDialog = ref(false)

const activeCategories = computed(() => ['全部', ...categories.value])
const isGuest = computed(() => !userStore.isLoggedIn)

async function fetchBooks() {
  loading.value = true
  try {
    const params = { limit: 200 }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (activeCategory.value !== '全部') params.category = activeCategory.value
    const res = await bookApi.list(params)
    books.value = res.data
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await bookApi.stats()
    stats.value = res.data
  } catch (e) { /* noop */ }
}

async function fetchCategories() {
  try {
    const res = await bookApi.categories()
    categories.value = res.data
  } catch (e) { /* noop */ }
}

function handleSearch() { fetchBooks() }
function selectCategory(cat) { activeCategory.value = cat; fetchBooks() }
function openBook(book) { selectedBook.value = book }
function closeDetail() { selectedBook.value = null }
function onBookAdded() { showAddDialog.value = false; fetchBooks(); fetchStats(); fetchCategories() }
function onBookUpdated() { fetchBooks(); fetchStats() }
function gotoLogin() { /* router.push('/login') but we'll import lazily */
  import('vue-router').then(({ useRouter }) => {
    useRouter().push('/login')
  })
}

onMounted(() => { fetchBooks(); fetchStats(); fetchCategories() })

// 状态文本
const statusText = {
  finished: '已读完',
  reading: '在读',
  unread: '未开始',
}

// 评分展示：豆瓣优先，否则手动
function displayRating(book) {
  if (book.douban_rating) return { score: book.douban_rating, source: 'douban' }
  if (book.manual_rating) return { score: book.manual_rating, source: 'manual' }
  return null
}

// 五角星：5 颗水平排列，每颗 12px
function starPath(i) {
  const x = (i - 1) * 12
  return `M${x + 6} 0 L${x + 7.4} 4 L${x + 12} 4 L${x + 8.3} 6.6 L${x + 9.7} 11 L${x + 6} 8.4 L${x + 2.3} 11 L${x + 3.7} 6.6 L${x + 0} 4 L${x + 4.6} 4 Z`
}
function starFill(i, score) {
  // Vue 3 v-for="i in 5" 实际 i 是 1,2,3,4,5 (renderList 源码: renderItem(i + 1, i, ...))
  // 豆瓣 10 分制 → 5 星: 1 星 = 2 分，四舍五入到整数颗
  // 例: 6.7→3, 7.5→4, 8.1→4, 8.2→4, 6.0→3
  const filled = Math.round(score / 2)
  return i <= filled ? 'var(--color-warning)' : 'transparent'
}
</script>

<template>
  <div class="library-page">
    <Topbar>
      <template #actions>
        <button v-if="!isGuest" class="btn btn-primary" @click="showAddDialog = true">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          添加图书
        </button>
      </template>
    </Topbar>

    <div v-if="isGuest" class="guest-banner">
      <span class="guest-dot"></span>
      你正以<strong>游客身份</strong>浏览，仅可查看书架。
      <a @click="gotoLogin">立即登录</a> 以使用全部功能。
    </div>

    <main class="main">
      <!-- 搜索区 -->
      <section class="search-section">
        <div class="search-header">
          <h2 class="search-title">我们的书架</h2>
          <p class="search-sub">
            家庭共 <span class="num">{{ stats.total }}</span> 本藏书 ·
            探索知识 · 享受阅读
          </p>
        </div>
        <form class="search-form" @submit.prevent="handleSearch">
          <span class="search-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4.3-4.3" />
            </svg>
          </span>
          <input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索书名、作者、ISBN（支持拼音首字母）..."
          />
          <button type="submit" class="search-btn">搜索</button>
        </form>
      </section>

      <!-- 分类标签 -->
      <div class="categories">
        <button
          v-for="cat in activeCategories"
          :key="cat"
          :class="['cat-chip', { active: activeCategory === cat }]"
          @click="selectCategory(cat)"
        >
          {{ cat }}
          <span v-if="cat !== '全部' && stats.categories?.find(s => s.category === cat)" class="cat-count">
            {{ stats.categories.find(s => s.category === cat).count }}
          </span>
        </button>
      </div>

      <!-- 列表头 -->
      <div class="list-head">
        <h3 class="list-title">
          {{ activeCategory === '全部' ? '全部藏书' : activeCategory }}
        </h3>
        <p class="list-count">共 <strong>{{ books.length }}</strong> 本</p>
      </div>

      <!-- 加载 -->
      <div v-if="loading" class="loading-row">
        <span class="spinner"></span>
        <span>正在翻阅书架...</span>
      </div>

      <!-- 图书卡片 -->
      <div v-else-if="books.length" class="book-grid">
        <article
          v-for="book in books"
          :key="book.id"
          class="book-card"
          @click="openBook(book)"
        >
          <div class="cover-wrap">
            <img
              v-if="book.cover_url"
              :src="book.cover_url"
              :alt="book.title"
              class="cover"
              referrerpolicy="no-referrer"
              @error="(e) => e.target.style.display='none'"
            />
            <div v-else class="cover-fallback">
              <div class="fallback-icon">
                <svg viewBox="0 0 32 32" width="44" height="44" fill="none" stroke="var(--color-primary)" stroke-width="1.4" stroke-linecap="round">
                  <path d="M6 5h13v22H6z" fill="var(--color-primary)" fill-opacity=".12" />
                  <path d="M19 5h7v22h-7z" />
                  <path d="M9 10h7M9 14h7M9 18h5" />
                </svg>
              </div>
              <span class="fallback-text">{{ book.title.slice(0, 4) }}</span>
            </div>

            <span v-if="displayRating(book)" class="rating-badge" :class="['rating-' + displayRating(book).source]">
              <svg class="rating-stars" viewBox="0 0 60 12" width="60" height="12" aria-hidden="true">
                <template v-for="i in 5" :key="i">
                  <path
                    :d="starPath(i)"
                    :fill="starFill(i, displayRating(book).score)"
                    stroke-width="0.4"
                    stroke-linejoin="round"
                  />
                </template>
              </svg>
              <span class="rating-score">{{ displayRating(book).score.toFixed(1) }}</span>
            </span>

            <span v-if="book.read_status && book.read_status !== 'unread'" class="status-tag" :class="`status-${book.read_status}`">
              {{ statusText[book.read_status] }}
            </span>
          </div>
          <div class="book-meta">
            <h3 class="book-title" :title="book.title">{{ book.title }}</h3>
            <p v-if="book.author" class="book-author">{{ book.author }}</p>
          </div>
        </article>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty">
        <div class="empty-illu">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none">
            <rect x="14" y="14" width="20" height="56" rx="2" fill="var(--color-primary)" fill-opacity=".15" stroke="var(--color-primary)" stroke-width="1.4"/>
            <rect x="38" y="22" width="20" height="48" rx="2" fill="var(--color-primary)" fill-opacity=".10" stroke="var(--color-primary)" stroke-width="1.4" opacity=".7"/>
            <rect x="60" y="32" width="14" height="38" rx="2" fill="var(--color-primary)" fill-opacity=".08" stroke="var(--color-primary)" stroke-width="1.4" opacity=".5"/>
          </svg>
        </div>
        <p class="empty-title">这里还没有书</p>
        <p class="empty-sub">从添加第一本书开始, 慢慢填满这面墙</p>
        <button v-if="!isGuest" class="btn btn-primary" @click="showAddDialog = true">
          添加第一本
        </button>
      </div>
    </main>

    <BookDetail v-if="selectedBook" :book="selectedBook" @close="closeDetail" @updated="onBookUpdated" />
    <AddBookDialog v-if="showAddDialog" @close="showAddDialog = false" @added="onBookAdded" />
  </div>
</template>

<style scoped>
.library-page { min-height: 100vh; display: flex; flex-direction: column; }

/* 游客横幅 */
.guest-banner {
  display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  background: var(--color-primary-tint);
  color: var(--color-text-secondary);
  padding: 10px 24px;
  font-size: var(--text-sm);
  border-bottom: 1px solid var(--color-primary-soft);
}
.guest-banner strong { color: var(--color-primary); font-weight: 600; margin: 0 2px; }
.guest-banner a { color: var(--color-primary); font-weight: 500; cursor: pointer; }
.guest-banner a:hover { text-decoration: underline; }
.guest-dot {
  width: 6px; height: 6px; background: var(--color-primary); border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 主体 */
.main {
  flex: 1;
  padding: var(--space-8) var(--space-6) var(--space-10);
  max-width: var(--content-max);
  margin: 0 auto;
  width: 100%;
}

/* === 搜索区 === */
.search-section {
  background: var(--color-bg-paper-deep);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-8) var(--space-6) var(--space-6);
  margin-bottom: var(--space-8);
  position: relative;
  overflow: hidden;
  background-image:
    radial-gradient(circle at 0% 0%, rgba(139, 105, 20, 0.05) 0%, transparent 40%),
    radial-gradient(circle at 100% 100%, rgba(139, 105, 20, 0.06) 0%, transparent 50%);
}
.search-section::before {
  content: '';
  position: absolute;
  top: var(--space-5);
  right: var(--space-6);
  width: 4px;
  height: 32px;
  background: var(--color-primary);
  border-radius: 2px;
  opacity: 0.4;
}
.search-header { text-align: center; margin-bottom: var(--space-6); }
.search-title {
  font-family: var(--font-serif);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
  letter-spacing: 0.04em;
}
.search-sub {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin: 0;
  letter-spacing: 0.02em;
}
.search-sub .num {
  font-family: var(--font-serif);
  font-weight: 700;
  color: var(--color-primary);
  font-size: var(--text-lg);
  margin: 0 4px;
}

.search-form {
  position: relative;
  display: flex;
  gap: var(--space-2);
  max-width: 640px;
  margin: 0 auto;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: 4px;
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-sm);
}
.search-form:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}
.search-icon {
  display: flex; align-items: center; justify-content: center;
  padding: 0 var(--space-3) 0 var(--space-4);
  color: var(--color-text-tertiary);
}
.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 0;
  font-size: var(--text-base);
  color: var(--color-text-primary);
}
.search-input:focus { box-shadow: none; }
.search-input::placeholder { color: var(--color-text-tertiary); }
.search-btn {
  background: var(--color-primary);
  color: var(--color-text-onPrimary);
  border: none;
  border-radius: var(--radius-pill);
  padding: 0 var(--space-6);
  font-weight: 500;
  font-family: inherit;
  font-size: var(--text-base);
  cursor: pointer;
  transition: all var(--transition-normal);
}
.search-btn:hover { background: var(--color-primary-hover); }

/* === 分类 === */
.categories {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  padding: 0;
}
.cat-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 16px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  font-family: inherit;
  transition: all var(--transition-normal);
  cursor: pointer;
}
.cat-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-tint);
}
.cat-chip.active {
  background: var(--color-primary);
  color: var(--color-text-onPrimary);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}
.cat-chip.active .cat-count {
  background: rgba(255, 252, 245, 0.2);
  color: var(--color-text-onPrimary);
}
.cat-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: var(--color-bg-sunken);
  color: var(--color-text-secondary);
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 500;
}

/* === 列表头 === */
.list-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin: var(--space-6) 0 var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}
.list-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}
.list-count { color: var(--color-text-secondary); margin: 0; font-size: var(--text-sm); }
.list-count strong { color: var(--color-text-primary); font-family: var(--font-serif); font-weight: 600; }

/* === 卡片网格 === */
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-5);
}

.book-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  animation: paperIn .4s ease both;
}
.book-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-book-hover);
  border-color: var(--color-border);
}
.book-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 4px;
  background: var(--color-primary);
  opacity: 0;
  transition: opacity var(--transition-normal);
}
.book-card:hover::after { opacity: 0.6; }

.cover-wrap {
  position: relative;
  aspect-ratio: 3/4;
  background: var(--color-bg-sunken);
  overflow: hidden;
}
.cover { width: 100%; height: 100%; object-fit: cover; display: block; }

.cover-fallback {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: var(--space-3);
  background: var(--color-bg-paper-deep);
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 11px,
      rgba(139, 105, 20, 0.04) 11px,
      rgba(139, 105, 20, 0.04) 12px
    );
}
.fallback-icon { opacity: 0.7; }
.fallback-text {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  letter-spacing: 0.1em;
}

.rating-badge {
  position: absolute;
  top: 8px; right: 8px;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px 5px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
  font-weight: 700;
  font-family: var(--font-serif);
  line-height: 1;
  border: 1.5px solid #fff;            /* 白色描边 = 任何封面都有边界 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}
.rating-stars { display: block; flex-shrink: 0; }
.rating-score {
  letter-spacing: 0.02em;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

/* 豆瓣评分：纯黑不透底（避免被深色封面"溶解"）+ 金色星徽 + 白色描边
   fill/stroke 不写在这里，交给 path 的内联 :fill 决定（满/半/空三态） */
.rating-badge.rating-douban {
  background: #1A1A1A;
}
.rating-badge.rating-douban .rating-stars path {
  stroke: #FFC940;          /* 描边统一金色，让空星也有边界可见 */
  stroke-width: 0.4;
}

/* 手动评分：浅色高对比底 + 主色金边 */
.rating-badge.rating-manual {
  background: #FFFDF7;
  color: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 2px 6px rgba(139, 105, 20, 0.18);
}

.status-tag {
  position: absolute;
  top: 8px; left: 8px;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
  font-family: var(--font-serif);
  letter-spacing: 0.04em;
}
.status-tag.status-finished {
  background: var(--color-success-soft);
  color: var(--color-success);
  border: 1px solid var(--color-success);
  border-left-width: 3px;
}
.status-tag.status-reading {
  background: var(--color-warning-soft);
  color: var(--color-warning);
  border: 1px solid var(--color-warning);
  border-left-width: 3px;
}

.book-meta { padding: var(--space-3) var(--space-4) var(--space-4); }
.book-title {
  margin: 0 0 4px;
  font-family: var(--font-serif);
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 38px;
}
.book-author {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 加载 */
.loading-row {
  display: flex; align-items: center; gap: var(--space-3); justify-content: center;
  padding: 80px 0;
  color: var(--color-text-secondary);
  font-family: var(--font-serif);
  font-style: italic;
}

/* 空状态 */
.empty {
  text-align: center;
  padding: 80px 20px;
  background: var(--color-bg-surface);
  border-radius: var(--radius-xl);
  border: 1px dashed var(--color-border-strong);
}
.empty-illu { margin-bottom: var(--space-5); opacity: 0.7; }
.empty-title {
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
}
.empty-sub {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-6);
  font-size: var(--text-sm);
}

@media (max-width: 768px) {
  .main { padding: var(--space-5) var(--space-4) var(--space-8); }
  .search-section { padding: var(--space-5) var(--space-4); }
  .search-title { font-size: var(--text-2xl); }
  .book-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: var(--space-3); }
  .book-title { font-size: var(--text-sm); min-height: 36px; }
  .book-author { font-size: var(--text-xs); }
}
</style>
