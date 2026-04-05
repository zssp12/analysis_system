/**
 * api/index.js — Axios 封装，统一所有后端接口调用
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 90000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截：统一错误格式
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      '请求失败'
    return Promise.reject(new Error(msg))
  }
)

// ── 新闻 ──────────────────────────────────────
export const getNews = (params) =>
  api.get('/news', { params })

export const refreshNews = () =>
  api.post('/news/refresh')

export const getRefreshStatus = () =>
  api.get('/news/refresh/status')

export const getCategories = () =>
  api.get('/news/categories')

export const getCategoryCounts = () =>
  api.get('/news/category-counts')

export const exportNews = ({ format, category }) =>
  api.get('/news/export', {
    params: { format, category: category !== 'all' ? category : undefined },
    responseType: 'blob',
  })

// ── 订阅源 ────────────────────────────────────
export const getSources = () =>
  api.get('/sources')

export const createSource = (data) =>
  api.post('/sources', data)

export const deleteSource = (id) =>
  api.delete(`/sources/${id}`)

export const toggleSource = (id) =>
  api.patch(`/sources/${id}/toggle`)

// ── 大模型 ────────────────────────────────────
// LLM 请求单独使用 180s 超时（推理模型耗时较长，全局 90s 不够）
const LLM_TIMEOUT = 180_000

export const getModels = () =>
  api.get('/llm/models')

export const analyzeNews = (data) =>
  api.post('/llm/analyze', data, { timeout: LLM_TIMEOUT })

export const analyzeCategory = (data) =>
  api.post('/llm/analyze-category', data, { timeout: LLM_TIMEOUT })

export const generateTweet = (data) =>
  api.post('/llm/generate-tweet', data, { timeout: LLM_TIMEOUT })

export default api
