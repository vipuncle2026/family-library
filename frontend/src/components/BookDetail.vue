<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { bookApi, readingApi, householdApi } from '../api'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const props = defineProps({ book: { type: Object, required: true } })
const emit = defineEmits(['close', 'updated'])

const router = useRouter()
const userStore = useUserStore()
const current = ref({ ...props.book })
const syncing = ref(false)
const saving = ref(false)
const showRecordPanel = ref(false)
const recordForm = ref({ progress: 0, duration_minutes: 0, current_page: 0, note: '', member_id: null })
const members = ref([])

const isGuest = computed(() => !userStore.isLoggedIn)
const isOwner = computed(() => userStore.user?.id === current.value.owner_id)
const canEdit = computed(() => !isGuest.value && (isOwner.value || userStore.user?.role === 'admin'))

const editing = ref(false)
const editForm = ref({})
const coverFileInput = ref(null)
const coverUploading = ref(false)
const coverPreview = ref(null)
const showRatingEditor = ref(false)
const ratingForm = ref({ douban_rating: 0, douban_rating_count: 0 })
const savingRating = ref(false)

const statusText = { unread: '未开始', reading: '在读中', finished: '已读完' }
const statusConfig = {
  unread:   { color: 'var(--color-text-tertiary)', bg: 'var(--color-bg-sunken)' },
  reading:  { color: 'var(--color-reading)',        bg: 'var(--color-warning-soft)' },
  finished: { color: 'var(--color-success)',        bg: 'var(--color-success-soft)' },
}

function startEdit() {
  editForm.value = {
    title: current.value.title,
    author: current.value.author || '',
    publisher: current.value.publisher || '',
    category: current.value.category || '',
    location: current.value.location || '',
    read_status: current.value.read_status || 'unread',
    cover_url: current.value.cover_url || '',
    summary: current.value.summary || '',
    owner_member_id: current.value.owner_member_id || null,
  }
  coverPreview.value = null
  editing.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    const res = await bookApi.update(current.value.id, editForm.value)
    current.value = { ...current.value, ...res.data }
    editing.value = false
    coverPreview.value = null
    emit('updated', current.value)
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function pickCoverFile() { coverFileInput.value?.click() }

function onCoverFileChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  const reader = new FileReader()
  reader.onload = (ev) => { coverPreview.value = ev.target.result }
  reader.readAsDataURL(f)
  uploadCover(f)
}

async function uploadCover(file) {
  if (file.size > 5 * 1024 * 1024) { alert('封面图不能超过 5MB'); return }
  coverUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await bookApi.uploadCover(fd)
    editForm.value.cover_url = res.data.url
  } catch (e) {
    alert(e.response?.data?.detail || '封面上传失败')
    coverPreview.value = null
  } finally {
    coverUploading.value = false
    if (coverFileInput.value) coverFileInput.value.value = ''
  }
}

function openRatingEditor() {
  ratingForm.value = {
    douban_rating: current.value.douban_rating || 0,
    douban_rating_count: current.value.douban_rating_count || 0,
  }
  showRatingEditor.value = true
}

async function saveManualRating() {
  if (ratingForm.value.douban_rating < 0 || ratingForm.value.douban_rating > 10) {
    return alert('评分需在 0-10 之间')
  }
  savingRating.value = true
  try {
    const payload = {
      douban_rating: ratingForm.value.douban_rating || null,
      douban_rating_count: ratingForm.value.douban_rating_count || null,
    }
    const res = await bookApi.update(current.value.id, payload)
    current.value = { ...current.value, ...res.data }
    showRatingEditor.value = false
    emit('updated', current.value)
  } catch (e) {
    alert(e.response?.data?.detail || '保存评分失败')
  } finally {
    savingRating.value = false
  }
}

async function clearManualRating() {
  if (!confirm('确定清空手动设置的评分吗?')) return
  try {
    const res = await bookApi.update(current.value.id, { clear_manual_rating: true })
    current.value = { ...current.value, ...res.data }
    emit('updated', current.value)
  } catch (e) {
    alert(e.response?.data?.detail || '清空失败')
  }
}

async function syncDouban() {
  if (!current.value.isbn) {
    alert('该书没有 ISBN, 无法同步')
    return
  }
  syncing.value = true
  try {
    const res = await bookApi.syncDouban(current.value.id)
    current.value = res.data
    emit('updated', current.value)
    alert('已同步豆瓣数据')
  } catch (e) {
    if (e.response?.status === 404) {
      if (confirm('豆瓣暂无该 ISBN 数据, 切到手动编辑补全评分/封面/简介吗?')) {
        editing.value = true
      }
    } else {
      alert(e.response?.data?.detail || '同步失败, 元数据源暂不可用')
    }
  } finally {
    syncing.value = false
  }
}

async function deleteBook() {
  if (!confirm(`确定删除《${current.value.title}》吗?`)) return
  try {
    await bookApi.remove(current.value.id)
    emit('updated', { _deleted: true, id: current.value.id })
    emit('close')
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

async function submitRecord() {
  if (recordForm.value.progress < 0 || recordForm.value.progress > 100) {
    return alert('进度需在 0-100')
  }
  try {
    await readingApi.create({ book_id: current.value.id, ...recordForm.value })
    showRecordPanel.value = false
    recordForm.value = { progress: 0, duration_minutes: 0, current_page: 0, note: '', member_id: null }
    const r = await bookApi.detail(current.value.id)
    current.value = r.data
    emit('updated', current.value)
    alert('阅读记录已保存')
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

function close() { emit('close') }
function handleOverlay(e) { if (e.target === e.currentTarget) close() }
function gotoLogin() { router.push('/login') }

const tags = computed(() => {
  if (!current.value.douban_tags) return []
  try { return JSON.parse(current.value.douban_tags) } catch { return [] }
})

const ownerMember = computed(() => {
  if (!current.value.owner_member_id) return null
  return members.value.find(m => m.id === current.value.owner_member_id) || null
})

const displayCover = computed(() => current.value.cover_url || null)

const isManual = computed(() => {
  return !!current.value.douban_rating && !current.value.douban_id
})

function onCoverError(e) { e.target.style.display = 'none' }

onMounted(async () => {
  if (userStore.isLoggedIn) {
    try {
      const r = await householdApi.my()
      members.value = r.data.members || []
    } catch {}
  }
  const handler = (e) => e.key === 'Escape' && close()
  window.addEventListener('keydown', handler)
  return () => window.removeEventListener('keydown', handler)
})

watch(() => props.book, (nb) => { current.value = { ...nb } })
</script>

<template>
  <div class="overlay" @click="handleOverlay">
    <div class="drawer" @click.stop>
      <header class="drawer-head">
        <div>
          <h2 class="drawer-title">图书详情</h2>
          <p class="drawer-sub">{{ editing ? '编辑图书信息' : '查看与记录' }}</p>
        </div>
        <button class="close-btn" @click="close" aria-label="关闭">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </header>

      <div class="drawer-body">
        <div v-if="!editing" class="view-mode">
          <div class="book-head">
            <div class="cover-box">
              <img
                v-if="displayCover"
                :src="displayCover"
                :alt="current.title"
                class="cover-lg"
                referrerpolicy="no-referrer"
                @error="onCoverError"
              />
              <div v-else class="cover-fallback-lg">
                <div class="cover-fallback-inner">
                  <svg viewBox="0 0 32 32" width="48" height="48" fill="none" stroke="var(--color-primary)" stroke-width="1.4">
                    <path d="M6 5h13v22H6z" fill="var(--color-primary)" fill-opacity=".10"/>
                    <path d="M19 5h7v22h-7z"/>
                  </svg>
                  <span class="cover-fallback-text">{{ current.title.slice(0, 3) }}</span>
                </div>
              </div>
            </div>
            <div class="book-meta">
              <h1 class="book-title">{{ current.title }}</h1>
              <p class="book-author" v-if="current.author">{{ current.author }}</p>

              <div v-if="current.douban_rating" class="douban-rating">
                <span class="rating-star">★</span>
                <span class="rating-num">{{ current.douban_rating.toFixed(1) }}</span>
                <span class="rating-count">{{ current.douban_rating_count || 0 }} 人评价</span>
                <span v-if="isManual" class="rating-source">手动</span>
                <span v-else class="rating-source">豆瓣</span>
              </div>
              <div v-else class="douban-rating empty">
                <span>暂无公开评分</span>
                <button v-if="canEdit" class="link-btn" @click="openRatingEditor">手动添加</button>
              </div>

              <div v-if="current.category" class="meta-tags">
                <span class="cat-badge">{{ current.category }}</span>
              </div>

              <div v-if="ownerMember" class="owner-tag">
                <span class="owner-dot" :style="{ background: ownerMember.avatar_color }"></span>
                归属：<strong>{{ ownerMember.display_name }}</strong>
                <span class="relation">{{ ownerMember.relation }}</span>
              </div>
            </div>
          </div>

          <dl class="info-list">
            <div v-if="current.publisher" class="info-row">
              <dt>出版社</dt>
              <dd>{{ current.publisher }}</dd>
            </div>
            <div v-if="current.pubdate" class="info-row">
              <dt>出版时间</dt>
              <dd>{{ current.pubdate }}</dd>
            </div>
            <div v-if="current.isbn" class="info-row">
              <dt>ISBN</dt>
              <dd class="mono">{{ current.isbn }}</dd>
            </div>
            <div v-if="current.pages" class="info-row">
              <dt>页数</dt>
              <dd>共 {{ current.pages }} 页</dd>
            </div>
            <div v-if="current.location" class="info-row">
              <dt>存放位置</dt>
              <dd>{{ current.location }}</dd>
            </div>
            <div class="info-row">
              <dt>阅读状态</dt>
              <dd>
                <span
                  class="status-pill"
                  :style="{
                    background: statusConfig[current.read_status]?.bg,
                    color: statusConfig[current.read_status]?.color,
                  }"
                >
                  <span class="dot" :style="{ background: statusConfig[current.read_status]?.color }"></span>
                  {{ statusText[current.read_status] }}
                </span>
              </dd>
            </div>
          </dl>

          <div v-if="tags.length" class="douban-tags">
            <h3 class="block-title">读者标签</h3>
            <div class="tag-list">
              <span v-for="t in tags" :key="t" class="tag">#{{ t }}</span>
            </div>
          </div>

          <div v-if="current.summary" class="summary">
            <h3 class="block-title">内容简介</h3>
            <p class="summary-text">{{ current.summary }}</p>
          </div>

          <div v-if="isGuest" class="guest-cta">
            <p>登录后可添加、编辑图书和记录阅读进度</p>
            <button class="btn btn-primary btn-sm" @click="gotoLogin">去登录</button>
          </div>

          <div v-if="canEdit" class="actions">
            <button class="btn btn-secondary" @click="startEdit">编辑</button>
            <button class="btn btn-secondary" @click="syncDouban" :disabled="syncing || !current.isbn">
              <span v-if="syncing" class="spinner"></span>
              <span v-else>同步豆瓣</span>
            </button>
            <button class="btn btn-secondary" @click="openRatingEditor">编辑评分</button>
            <button class="btn btn-primary" @click="showRecordPanel = !showRecordPanel">记录阅读</button>
            <button class="btn-link danger" @click="deleteBook">删除</button>
          </div>

          <div v-if="showRatingEditor" class="form-panel">
            <h3 class="block-title">手动设置评分</h3>
            <p class="block-hint">豆瓣抓不到时, 可自己录入 (0-10 分制)</p>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">评分 (★)</label>
                <input v-model.number="ratingForm.douban_rating" type="number" min="0" max="10" step="0.1" class="input" />
              </div>
              <div class="field">
                <label class="field-label">评价人数</label>
                <input v-model.number="ratingForm.douban_rating_count" type="number" min="0" class="input" placeholder="可选" />
              </div>
            </div>
            <div class="form-actions">
              <button v-if="current.douban_rating" class="btn-link danger" @click="clearManualRating">清空评分</button>
              <span style="flex:1"></span>
              <button class="btn btn-ghost" @click="showRatingEditor = false">取消</button>
              <button class="btn btn-primary" :disabled="savingRating" @click="saveManualRating">
                <span v-if="savingRating" class="spinner"></span>
                <span v-else>保存</span>
              </button>
            </div>
          </div>

          <div v-if="showRecordPanel" class="form-panel">
            <h3 class="block-title">记录阅读进度</h3>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">阅读进度 (%)</label>
                <input v-model.number="recordForm.progress" class="input" type="number" min="0" max="100" />
              </div>
              <div class="field">
                <label class="field-label">当前页</label>
                <input v-model.number="recordForm.current_page" class="input" type="number" min="0" />
              </div>
              <div class="field">
                <label class="field-label">本次时长 (分钟)</label>
                <input v-model.number="recordForm.duration_minutes" class="input" type="number" min="0" />
              </div>
            </div>
            <div class="field">
              <label class="field-label">笔记</label>
              <textarea v-model="recordForm.note" class="input" rows="2" placeholder="今天读了什么..."></textarea>
            </div>
            <div class="field" v-if="members.length">
              <label class="field-label">谁在读</label>
              <select v-model="recordForm.member_id" class="input">
                <option :value="null">未指定</option>
                <option v-for="m in members" :key="m.id" :value="m.id">
                  {{ m.display_name }}（{{ m.relation }}）
                </option>
              </select>
            </div>
            <div class="form-actions">
              <span style="flex:1"></span>
              <button class="btn btn-ghost" @click="showRecordPanel = false">取消</button>
              <button class="btn btn-primary" @click="submitRecord">保存记录</button>
            </div>
          </div>
        </div>

        <div v-else class="edit-mode">
          <div class="form">
            <div class="field">
              <label class="field-label">书名 <span class="req">*</span></label>
              <input v-model="editForm.title" class="input" />
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">作者</label>
                <input v-model="editForm.author" class="input" />
              </div>
              <div class="field">
                <label class="field-label">出版社</label>
                <input v-model="editForm.publisher" class="input" />
              </div>
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">分类</label>
                <input v-model="editForm.category" class="input" placeholder="小说 / 历史 / ..." />
              </div>
              <div class="field">
                <label class="field-label">存放位置</label>
                <input v-model="editForm.location" class="input" placeholder="书房 / 客厅书柜..." />
              </div>
            </div>
            <div class="field">
              <label class="field-label">阅读状态</label>
              <select v-model="editForm.read_status" class="input">
                <option value="unread">未开始</option>
                <option value="reading">在读</option>
                <option value="finished">已读完</option>
              </select>
            </div>
            <div class="field" v-if="members.length">
              <label class="field-label">归属成员</label>
              <select v-model="editForm.owner_member_id" class="input">
                <option :value="null">未归属 / 全家共读</option>
                <option v-for="m in members" :key="m.id" :value="m.id">
                  {{ m.display_name }}（{{ m.relation }}）
                </option>
              </select>
            </div>

            <div class="field">
              <label class="field-label">封面图</label>
              <div class="cover-editor">
                <div class="cover-preview">
                  <img v-if="coverPreview || editForm.cover_url" :src="coverPreview || editForm.cover_url" @error="onCoverError" referrerpolicy="no-referrer" />
                  <span v-else class="cover-fallback-sm">无封面</span>
                </div>
                <div class="cover-actions">
                  <input ref="coverFileInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" style="display:none" @change="onCoverFileChange" />
                  <button type="button" class="btn btn-secondary btn-sm" :disabled="coverUploading" @click="pickCoverFile">
                    <span v-if="coverUploading" class="spinner"></span>
                    <span v-else>本地上传</span>
                  </button>
                  <span class="cover-hint">JPG/PNG/WebP · ≤5MB</span>
                </div>
              </div>
              <input v-model="editForm.cover_url" class="input mt-8" placeholder="或填图片 URL" />
            </div>

            <div class="field">
              <label class="field-label">简介</label>
              <textarea v-model="editForm.summary" class="input" rows="4"></textarea>
            </div>
            <div class="form-actions">
              <span style="flex:1"></span>
              <button class="btn btn-ghost" @click="editing = false; coverPreview = null">取消</button>
              <button class="btn btn-primary" :disabled="saving" @click="saveEdit">
                <span v-if="saving" class="spinner"></span>
                <span v-else>保存</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer {
  position: absolute; right: 0; top: 0;
  width: 100%; max-width: 600px; height: 100vh;
  background: var(--color-bg-elevated);
  border-left: 1px solid var(--color-border);
  box-shadow: -16px 0 48px rgba(44, 33, 24, 0.16);
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; flex-direction: column;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

.drawer-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-surface);
  flex-shrink: 0;
}
.drawer-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1);
  letter-spacing: 0.04em;
}
.drawer-sub { font-size: var(--text-sm); color: var(--color-text-secondary); margin: 0; }
.close-btn {
  width: 36px; height: 36px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-secondary);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-normal);
  flex-shrink: 0;
  padding: 0;
}
.close-btn:hover {
  background: var(--color-bg-sunken);
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

.drawer-body { flex: 1; overflow-y: auto; padding: var(--space-6); }

/* === 头部 === */
.book-head { display: flex; gap: var(--space-5); margin-bottom: var(--space-6); }
.cover-box { flex-shrink: 0; width: 130px; }
.cover-lg {
  width: 130px; aspect-ratio: 3/4;
  object-fit: cover;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-book);
  display: block;
}
.cover-fallback-lg {
  width: 130px; aspect-ratio: 3/4;
  background: var(--color-bg-paper-deep);
  background-image: repeating-linear-gradient(
    0deg,
    transparent, transparent 11px,
    rgba(139, 105, 20, 0.05) 11px, rgba(139, 105, 20, 0.05) 12px
  );
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--color-border);
}
.cover-fallback-inner { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); }
.cover-fallback-text { font-family: var(--font-serif); font-size: var(--text-sm); color: var(--color-primary); }

.book-meta { flex: 1; min-width: 0; }
.book-title {
  font-family: var(--font-serif);
  margin: 0 0 var(--space-2);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
  letter-spacing: 0.02em;
}
.book-author { margin: 0 0 var(--space-3); color: var(--color-text-secondary); font-size: var(--text-sm); }

.douban-rating {
  display: flex; align-items: baseline; gap: 6px; margin-bottom: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-paper-deep);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.rating-star { color: var(--color-warning); font-size: var(--text-lg); }
.rating-num {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}
.rating-count { font-size: var(--text-xs); color: var(--color-text-secondary); }
.rating-source {
  font-size: var(--text-xs);
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-tint);
  color: var(--color-primary);
  font-weight: 500;
  font-family: var(--font-serif);
}
.douban-rating.empty {
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  font-style: italic;
  font-family: var(--font-serif);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-sunken);
}
.link-btn {
  background: transparent;
  border: none;
  color: var(--color-primary);
  font-size: var(--text-sm);
  text-decoration: underline;
  cursor: pointer;
  padding: 0 0 0 var(--space-2);
  font-family: inherit;
}

.meta-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: var(--space-2); }
.cat-badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
  font-family: var(--font-serif);
}

.owner-tag {
  display: inline-flex; align-items: center; gap: var(--space-2);
  margin-top: var(--space-2);
  padding: 4px 10px;
  background: var(--color-bg-sunken);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}
.owner-tag strong { color: var(--color-text-primary); font-weight: 600; font-family: var(--font-serif); }
.owner-tag .relation { color: var(--color-primary); }
.owner-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* === 信息列表 === */
.info-list {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-3);
  margin: 0 0 var(--space-5);
}
.info-row {
  display: flex;
  padding: var(--space-2) 0;
  border-bottom: 1px dashed var(--color-border-soft);
  font-size: var(--text-sm);
}
.info-row:last-child { border-bottom: none; }
.info-row dt {
  width: 80px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  font-family: var(--font-serif);
  font-style: italic;
}
.info-row dd { margin: 0; color: var(--color-text-primary); }
.mono { font-family: ui-monospace, "SF Mono", Consolas, monospace; font-size: var(--text-sm); }

.status-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 500;
  font-family: var(--font-serif);
}
.status-pill .dot { width: 6px; height: 6px; border-radius: 50%; }

/* === 简介 & 标签 === */
.douban-tags, .summary { margin-top: var(--space-5); }
.block-title {
  font-family: var(--font-serif);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2);
  padding-left: var(--space-3);
  position: relative;
}
.block-title::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 14px;
  background: var(--color-primary);
  border-radius: 2px;
}
.tag-list { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.tag {
  padding: 2px 10px;
  background: var(--color-bg-sunken);
  color: var(--color-text-secondary);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-family: var(--font-serif);
}
.summary-text {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  line-height: 1.8;
  white-space: pre-wrap;
  font-family: var(--font-serif);
  padding: var(--space-3);
  background: var(--color-bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
}

.guest-cta {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3);
  margin-top: var(--space-5);
  padding: var(--space-4);
  background: var(--color-primary-tint);
  border: 1px dashed var(--color-primary-soft);
  border-radius: var(--radius-md);
}
.guest-cta p { margin: 0; color: var(--color-text-primary); font-size: var(--text-sm); }

.actions {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
  display: flex; flex-wrap: wrap; gap: var(--space-2);
  align-items: center;
}

.btn-link {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  padding: 6px 10px;
  border-radius: var(--radius-md);
  font-family: inherit;
  transition: all var(--transition-fast);
}
.btn-link:hover { background: var(--color-bg-sunken); color: var(--color-text-primary); }
.btn-link.danger { color: var(--color-danger); }
.btn-link.danger:hover { background: var(--color-danger-soft); }

/* === 表单面板 === */
.form-panel {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.block-hint { font-size: var(--text-xs); color: var(--color-text-tertiary); margin: 0 0 var(--space-3); font-style: italic; font-family: var(--font-serif); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.field { margin-bottom: var(--space-3); }
.req { color: var(--color-danger); }
.form-actions { display: flex; gap: var(--space-2); align-items: center; margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--color-border); }

textarea.input { resize: vertical; font-family: var(--font-serif); }

.cover-editor { display: flex; align-items: center; gap: var(--space-3); }
.cover-preview {
  width: 64px; height: 90px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-sunken);
  overflow: hidden;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px dashed var(--color-border-strong);
}
.cover-preview img { width: 100%; height: 100%; object-fit: cover; }
.cover-fallback-sm { font-size: var(--text-xs); color: var(--color-text-tertiary); }
.cover-actions { display: flex; flex-direction: column; gap: 4px; }
.cover-hint { font-size: var(--text-xs); color: var(--color-text-tertiary); }
.mt-8 { margin-top: var(--space-2); }

@media (max-width: 640px) {
  .drawer { max-width: 100%; }
  .book-head { flex-direction: column; align-items: center; text-align: center; }
  .cover-box, .cover-lg, .cover-fallback-lg { width: 140px; }
  .douban-rating, .meta-tags, .owner-tag { justify-content: center; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
