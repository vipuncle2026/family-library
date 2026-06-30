import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (location.pathname !== '/login') {
        location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api

// 业务封装
export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

export const bookApi = {
  list: (params) => api.get('/books', { params }),
  detail: (id) => api.get(`/books/${id}`),
  create: (data) => api.post('/books', data),
  update: (id, data) => api.put(`/books/${id}`, data),
  remove: (id) => api.delete(`/books/${id}`),
  stats: () => api.get('/books/stats'),
  categories: () => api.get('/books/categories'),
  doubanSearch: (q) => api.get('/books/douban/search', { params: { q } }),
  doubanByIsbn: (isbn) => api.get(`/books/douban/isbn/${isbn}`),
  syncDouban: (id) => api.post(`/books/${id}/sync-douban`),
  syncDoubanByDoubanId: (id, doubanId) => api.post(`/books/${id}/sync-douban-by-id`, { douban_id: doubanId }),
  uploadCover: (formData) => api.post('/books/upload-cover', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  }),
  metaCacheStats: () => api.get('/books/meta-cache/stats'),
  clearMetaCache: () => api.delete('/books/meta-cache'),
}

export const readingApi = {
  records: (params) => api.get('/reading/records', { params }),
  create: (data) => api.post('/reading/records', data),
  stats: (params) => api.get('/reading/stats', { params }),
}

export const householdApi = {
  my: () => api.get('/households/me'),
  availableUsers: () => api.get('/households/users/available'),
  addMember: (data) => api.post('/households/me/members', data),
  updateMember: (id, data) => api.patch(`/households/me/members/${id}`, data),
  removeMember: (id) => api.delete(`/households/me/members/${id}`),
}
