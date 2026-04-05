/**
 * stores/sourceStore.js — 订阅源管理状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getSources,
  createSource,
  deleteSource,
  toggleSource,
} from '../api/index'

export const useSourceStore = defineStore('source', () => {
  const sources = ref([])
  const loading = ref(false)

  async function fetchSources() {
    loading.value = true
    try {
      const { data } = await getSources()
      sources.value = data
    } finally {
      loading.value = false
    }
  }

  async function addSource(sourceData) {
    const { data } = await createSource(sourceData)
    sources.value.unshift(data)
    return data
  }

  async function removeSource(id) {
    await deleteSource(id)
    sources.value = sources.value.filter((s) => s.id !== id)
  }

  async function toggle(id) {
    const { data } = await toggleSource(id)
    const src = sources.value.find((s) => s.id === id)
    if (src) src.enabled = data.enabled
  }

  return { sources, loading, fetchSources, addSource, removeSource, toggle }
})
