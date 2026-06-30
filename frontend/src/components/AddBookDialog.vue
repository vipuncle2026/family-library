<script setup>
import { ref, computed } from 'vue'
import { bookApi } from '../api'

const emit = defineEmits(['close', 'added'])

const mode = ref('isbn')
const isbn = ref('')
const searchResults = ref([])
const searching = ref(false)
const syncing = ref(false)
const selectedDouban = ref(null)
const loadingMsg = ref('')
const errMsg = ref('')

const manualForm = ref({
  title: '', author: '', publisher: '', isbn: '',
  category: '', location: '', cover_url: '', summary: '',
  pages: null, pubdate: '',
  douban_rating: 0, douban_rating_count: 0,
})

const coverPreview = ref(null)
const coverUploading = ref(false)
const coverFileInput = ref(null)

const isISBN13 = computed(() => /^\d{13}$/.test(isbn.value.replace(/-/g, '').replace(/\s/g, '')))

async function searchISBN() {
  const cleaned = isbn.value.replace(/-/g, '').replace(/\s/g, '')
  if (!cleaned) return
  errMsg.value = ''
  searching.value = true
  searchResults.value = []
  loadingMsg.value = '正在查询元数据 (豆瓣)...'
  try {
    const r1 = await bookApi.doubanByIsbn(cleaned)
    if (r1?.data) {
      searchResults.value = [r1.data]
      selectedDouban.value = r1.data
      loadingMsg.value = r1.data.rating
        ? `找到匹配 (★ ${r1.data.rating.toFixed(1)}), 请确认; 缺啥可在手动模式补`
        : '找到匹配, 但豆瓣暂无评分, 可在手动模式补'
    } else {
      loadingMsg.value = '暂未找到该 ISBN 数据, 可切到手动模式'
    }
  } catch (e) {
    if (e.response?.status === 404) {
      loadingMsg.value = '豆瓣暂无该 ISBN, 帮你切到手动模式, ISBN 已自动填好'
      switchToManualWithIsbn()
    } else {
      errMsg.value = '查询失败, 可切到手动模式'
      loadingMsg.value = '元数据源暂不可用, 可切到手动模式'
    }
  } finally {
    searching.value = false
  }
}

function switchToManualWithIsbn() {
  const cleaned = isbn.value.replace(/-/g, '').replace(/\s/g, '')
  manualForm.value.isbn = cleaned
  mode.value = 'manual'
}

function switchToManualPrefilled(item) {
  const cleaned = isbn.value.replace(/-/g, '').replace(/\s/g, '')
  manualForm.value = {
    title: item.title || '',
    author: item.author || '',
    publisher: item.publisher || '',
    isbn: cleaned,
    category: '',
    location: '',
    cover_url: item.cover_url || '',
    summary: item.summary || '',
    pages: item.pages || null,
    pubdate: item.pubdate || '',
    douban_rating: item.rating || 0,
    douban_rating_count: item.rating_count || 0,
  }
  if (item.cover_url) coverPreview.value = item.cover_url
  mode.value = 'manual'
}

async function addFromDouban(item) {
  errMsg.value = ''
  syncing.value = true
  try {
    const cleanedIsbn = isbn.value.replace(/-/g, '').replace(/\s/g, '')
    const payload = {
      // 优先用 ISBN, 失败回退 douban_id; 都不行才用手动填
      isbn: item.douban_id ? null : (cleanedIsbn || null),
      title: item.title,
      author: item.author || '',
      publisher: item.publisher || '',
      pubdate: item.pubdate || '',
      pages: item.pages || null,
      cover_url: item.cover_url || '',
      summary: item.summary || '',
      category: '',
      location: '',
      // 关键: 豆瓣评分/评分人数/豆瓣 ID 必须随 create 一起落库,
      // 否则 sync-douban 步骤只对有 ISBN 的书生效, 无 ISBN 的书评分就会丢
      douban_id: item.douban_id || null,
      douban_rating: item.rating || null,
      douban_rating_count: item.rating_count || null,
    }
    const r = await bookApi.create(payload)
    // 即便 create 时已写, 再调一次 sync 让 last_douban_sync 刷新 (兼带兜底)
    if (r.data.isbn) {
      try { await bookApi.syncDouban(r.data.id) } catch (syncErr) { console.warn('sync-douban 失败 (非阻塞):', syncErr) }
    } else if (r.data.douban_id) {
      try { await bookApi.syncDoubanByDoubanId(r.data.id, r.data.douban_id) } catch (syncErr) { console.warn('sync-by-douban-id 失败 (非阻塞):', syncErr) }
    }
    emit('added', r.data)
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '添加失败'
  } finally {
    syncing.value = false
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
  if (file.size > 5 * 1024 * 1024) { errMsg.value = '封面图不能超过 5MB'; return }
  coverUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await bookApi.uploadCover(fd)
    manualForm.value.cover_url = res.data.url
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '封面上传失败'
    coverPreview.value = null
  } finally {
    coverUploading.value = false
    if (coverFileInput.value) coverFileInput.value.value = ''
  }
}

async function addManual() {
  errMsg.value = ''
  if (!manualForm.value.title) { errMsg.value = '书名不能为空'; return }
  if (manualForm.value.douban_rating && (manualForm.value.douban_rating < 0 || manualForm.value.douban_rating > 10)) {
    errMsg.value = '评分需在 0-10 之间'; return
  }
  try {
    const payload = {
      ...manualForm.value,
      read_status: 'unread',
      pages: manualForm.value.pages || null,
      douban_rating: manualForm.value.douban_rating || null,
      douban_rating_count: manualForm.value.douban_rating_count || null,
    }
    const r = await bookApi.create(payload)
    emit('added', r.data)
  } catch (e) {
    errMsg.value = e.response?.data?.detail || '添加失败'
  }
}

function close() { emit('close') }
function handleOverlay(e) { if (e.target === e.currentTarget) close() }
</script>

<template>
  <div class="overlay" @click="handleOverlay">
    <div class="modal" @click.stop>
      <header class="modal-head">
        <div>
          <h2 class="modal-title">添加图书</h2>
          <p class="modal-sub">扫码 / ISBN 一键入库，或手动补全</p>
        </div>
        <button class="close-btn" @click="close" aria-label="关闭">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </header>

      <div class="modal-body">
        <div class="tabs">
          <button :class="['tab', { active: mode === 'isbn' }]" @click="mode = 'isbn'">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
              <path d="M3 5v14M7 5v14M11 5v14M15 5v14M19 5v14"/>
            </svg>
            扫码 / ISBN
          </button>
          <button :class="['tab', { active: mode === 'manual' }]" @click="mode = 'manual'">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4v16h16v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            手动录入
          </button>
        </div>

        <div v-if="errMsg" class="err-msg">{{ errMsg }}</div>

        <!-- ISBN 模式 -->
        <div v-if="mode === 'isbn'" class="isbn-mode">
          <div class="field">
            <label class="field-label">输入 ISBN 码</label>
            <div class="isbn-input-row">
              <input
                v-model="isbn"
                class="input"
                placeholder="9787xxxxxxxxx (13位)"
                @keyup.enter="searchISBN"
              />
              <button class="btn btn-primary" :disabled="searching || !isbn" @click="searchISBN">
                <span v-if="searching" class="spinner spinner-light"></span>
                <span v-else>查 找</span>
              </button>
            </div>
            <p class="hint">支持扫条码后粘贴, 也可手动输入 13 位 ISBN。豆瓣会尽量拉评分/封面/简介, 若没拉到可在「手动录入」补充。</p>
          </div>

          <div v-if="loadingMsg" class="status-msg">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
              <circle cx="12" cy="12" r="9"/>
              <path d="M12 8v4l3 2"/>
            </svg>
            {{ loadingMsg }}
          </div>

          <div v-if="searchResults.length" class="result-list">
            <div
              v-for="item in searchResults"
              :key="item.douban_id"
              :class="['result-card', { selected: selectedDouban?.douban_id === item.douban_id }]"
              @click="selectedDouban = item"
            >
              <div class="result-cover-wrap">
                <img v-if="item.cover_url" :src="item.cover_url" class="result-cover" referrerpolicy="no-referrer" @error="(e) => e.target.style.display='none'" />
                <div v-else class="result-cover-fallback">
                  <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="var(--color-text-tertiary)" stroke-width="1.4">
                    <path d="M5 5h13v14H5z" fill="var(--color-bg-sunken)"/>
                    <path d="M18 5h2v14h-2"/>
                  </svg>
                </div>
              </div>
              <div class="result-meta">
                <h4 class="result-title">{{ item.title }}</h4>
                <p v-if="item.author" class="r-author">{{ item.author }}</p>
                <p v-if="item.publisher" class="r-pub">{{ item.publisher }}<span v-if="item.pubdate"> · {{ item.pubdate }}</span></p>
                <div v-if="item.rating" class="r-rating">
                  <span class="star">★</span> {{ item.rating.toFixed(1) }}
                  <span class="r-count">({{ item.rating_count }} 人)</span>
                </div>
                <div v-else class="r-rating empty">豆瓣暂无评分, 可在手动模式补</div>
              </div>
            </div>

            <div class="action-row">
              <button class="btn btn-ghost btn-sm" @click="searchResults = []; selectedDouban = null">重新搜索</button>
              <button class="btn btn-secondary btn-sm" @click="switchToManualPrefilled(selectedDouban)">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4v16h16v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                补全信息
              </button>
              <button class="btn btn-primary" :disabled="!selectedDouban || syncing" @click="addFromDouban(selectedDouban)">
                <span v-if="syncing" class="spinner spinner-light"></span>
                <span v-else>加入书架</span>
              </button>
            </div>
          </div>

          <div v-else-if="!loadingMsg" class="empty-tip">
            <div class="empty-icon">
              <svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="var(--color-text-tertiary)" stroke-width="1.4" stroke-linecap="round">
                <path d="M8 8h4v32H8zM14 8h4v32h-4zM20 8l4-1 4 34-4 1z"/>
              </svg>
            </div>
            <p>输入 ISBN 后按回车，系统自动从豆瓣查找</p>
          </div>
        </div>

        <!-- 手动录入 -->
        <div v-else class="manual-mode">
          <div class="form">
            <div class="field">
              <label class="field-label">书名 <span class="req">*</span></label>
              <input v-model="manualForm.title" class="input" placeholder="必填" />
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">作者</label>
                <input v-model="manualForm.author" class="input" />
              </div>
              <div class="field">
                <label class="field-label">出版社</label>
                <input v-model="manualForm.publisher" class="input" />
              </div>
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">ISBN</label>
                <input v-model="manualForm.isbn" class="input" />
              </div>
              <div class="field">
                <label class="field-label">页数</label>
                <input v-model.number="manualForm.pages" type="number" class="input" />
              </div>
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">分类</label>
                <input v-model="manualForm.category" class="input" placeholder="小说 / 历史 / ..." />
              </div>
              <div class="field">
                <label class="field-label">存放位置</label>
                <input v-model="manualForm.location" class="input" placeholder="书房书架..." />
              </div>
            </div>
            <div class="grid-2">
              <div class="field">
                <label class="field-label">豆瓣评分 (0-10)</label>
                <input v-model.number="manualForm.douban_rating" type="number" min="0" max="10" step="0.1" class="input" placeholder="如 8.5" />
              </div>
              <div class="field">
                <label class="field-label">评价人数</label>
                <input v-model.number="manualForm.douban_rating_count" type="number" min="0" class="input" placeholder="可选" />
              </div>
            </div>

            <div class="field">
              <label class="field-label">封面图</label>
              <div class="cover-editor">
                <div class="cover-preview">
                  <img v-if="coverPreview || manualForm.cover_url" :src="coverPreview || manualForm.cover_url" referrerpolicy="no-referrer" @error="(e) => e.target.style.display='none'" />
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
              <input v-model="manualForm.cover_url" class="input mt-8" placeholder="或填图片 URL" />
            </div>

            <div class="form-actions">
              <button class="btn btn-ghost" @click="close">取消</button>
              <button class="btn btn-primary" @click="addManual">加入书架</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 92%; max-width: 600px; max-height: 90vh;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  display: flex; flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  animation: modalIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes modalIn {
  from { transform: translate(-50%, -48%); opacity: 0; }
  to   { transform: translate(-50%, -50%); opacity: 1; }
}

.modal-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-surface);
}
.modal-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1);
  letter-spacing: 0.04em;
}
.modal-sub { font-size: var(--text-sm); color: var(--color-text-secondary); margin: 0; }
.close-btn {
  width: 32px; height: 32px;
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

.modal-body { flex: 1; overflow-y: auto; padding: var(--space-5) var(--space-6) var(--space-6); }

.tabs {
  display: flex; gap: 4px;
  background: var(--color-bg-sunken);
  padding: 4px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
}
.tab {
  flex: 1;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  font-family: inherit;
  transition: all var(--transition-normal);
  cursor: pointer;
}
.tab.active {
  background: var(--color-bg-elevated);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.err-msg {
  padding: 10px 12px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
  border-left: 3px solid var(--color-danger);
}

.field { margin-bottom: var(--space-4); }
.req { color: var(--color-danger); }
.hint { margin: var(--space-2) 0 0; font-size: var(--text-xs); color: var(--color-text-tertiary); line-height: 1.6; }

.isbn-input-row { display: flex; gap: var(--space-2); }
.isbn-input-row .input { flex: 1; }

.status-msg {
  display: flex; align-items: center; gap: var(--space-2);
  padding: 10px 14px;
  background: var(--color-primary-tint);
  color: var(--color-text-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin: var(--space-3) 0;
  border-left: 3px solid var(--color-primary);
  font-family: var(--font-serif);
  font-style: italic;
}

.empty-tip {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--color-text-tertiary);
}
.empty-tip p { margin: var(--space-3) 0 0; font-size: var(--text-sm); font-family: var(--font-serif); font-style: italic; }
.empty-icon { opacity: 0.6; }

.result-list { margin-top: var(--space-4); }
.result-card {
  display: flex; gap: var(--space-3);
  padding: var(--space-3);
  border: 1.5px solid var(--color-border);
  background: var(--color-bg-surface);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-bottom: var(--space-3);
}
.result-card:hover { border-color: var(--color-border-strong); }
.result-card.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-tint);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}
.result-cover-wrap { flex-shrink: 0; }
.result-cover { width: 64px; height: 90px; object-fit: cover; border-radius: var(--radius-sm); display: block; }
.result-cover-fallback {
  width: 64px; height: 90px;
  background: var(--color-bg-sunken);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
}
.result-meta { flex: 1; min-width: 0; }
.result-title {
  font-family: var(--font-serif);
  margin: 0 0 var(--space-1);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
}
.r-author { margin: 0 0 4px; color: var(--color-text-secondary); font-size: var(--text-sm); }
.r-pub { margin: 0 0 4px; color: var(--color-text-tertiary); font-size: var(--text-xs); }
.r-rating {
  color: var(--color-warning);
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: var(--font-serif);
  display: inline-flex; align-items: center; gap: 4px;
}
.r-rating .star { font-size: var(--text-md); }
.r-rating .r-count { color: var(--color-text-tertiary); font-weight: 400; font-size: var(--text-xs); }
.r-rating.empty { color: var(--color-text-tertiary); font-weight: 400; font-style: italic; font-family: var(--font-serif); }

.action-row { display: flex; gap: var(--space-2); justify-content: flex-end; margin-top: var(--space-3); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.form-actions {
  display: flex; gap: var(--space-2); justify-content: flex-end;
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

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

.spinner-light { border-color: rgba(255, 252, 245, 0.4); border-top-color: var(--color-text-onPrimary); }

@media (max-width: 640px) {
  .modal { max-height: 95vh; width: 95%; }
  .grid-2 { grid-template-columns: 1fr; }
  .modal-head, .modal-body { padding-left: var(--space-4); padding-right: var(--space-4); }
}
</style>
