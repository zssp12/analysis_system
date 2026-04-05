/**
 * stores/newsStore.js — 新闻列表、类别、刷新状态的全局状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getNews,
  refreshNews,
  getRefreshStatus,
  getCategories,
  getCategoryCounts,
  exportNews,
} from '../api/index'

export const useNewsStore = defineStore('news', () => {
  const newsList      = ref([])
  const dbCategories  = ref([])           // 数据库中已有的类别
  const countMap      = ref({})           // { all: N, 科技: M, ... } 各类别准确数量
  const currentCategory = ref('all')
  const loading       = ref(false)
  const error         = ref(null)
  const refreshStatus = ref({
    status: 'idle',
    last_refresh: null,
    added: 0,
    error: null,
    total: 0,
    done: 0,
  })

  /** 当前已有类别（含 all + 数据库中的） */
  const categories = computed(() => {
    const set = new Set([
      ...dbCategories.value,
      ...newsList.value.map((n) => n.category),
    ])
    return ['all', ...Array.from(set).sort()]
  })

  /** 获取新闻列表（按类别） */
  async function fetchNews(category = 'all') {
    loading.value = true
    error.value = null
    currentCategory.value = category
    try {
      const params = {}
      if (category && category !== 'all') params.category = category
      const { data } = await getNews(params)
      newsList.value = data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  /** 获取数据库中所有类别 */
  async function fetchCategories() {
    try {
      const { data } = await getCategories()
      dbCategories.value = data
    } catch (_) {}
  }

  /** 获取各类别准确数量（从后端统计，不受分页 limit 影响） */
  async function fetchCounts() {
    try {
      const { data } = await getCategoryCounts()
      countMap.value = data
    } catch (_) {}
  }

  /** 触发后台刷新，并轮询状态 */
  let _pollTimer = null
  async function triggerRefresh() {
    if (refreshStatus.value.status === 'refreshing') return
    await refreshNews()
    refreshStatus.value.status = 'refreshing'
    _startPolling()
  }

  function _startPolling() {
    if (_pollTimer) clearInterval(_pollTimer)
    _pollTimer = setInterval(async () => {
      try {
        const { data } = await getRefreshStatus()
        refreshStatus.value = data
        if (data.status !== 'refreshing') {
          clearInterval(_pollTimer)
          _pollTimer = null
          if (data.status === 'idle') {
            await fetchNews(currentCategory.value)
            await fetchCategories()
            await fetchCounts()
          }
        }
      } catch (_) {
        clearInterval(_pollTimer)
        _pollTimer = null
      }
    }, 1500)
  }

  /** 导出新闻列表 */
  async function doExport(format) {
    try {
      const response = await exportNews({
        format,
        category: currentCategory.value,
      })
      const blob = new Blob([response.data])
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `news_export.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = e.message
    }
  }

  return {
    newsList,
    dbCategories,
    countMap,
    currentCategory,
    categories,
    loading,
    error,
    refreshStatus,
    fetchNews,
    fetchCategories,
    fetchCounts,
    triggerRefresh,
    doExport,
  }
})
