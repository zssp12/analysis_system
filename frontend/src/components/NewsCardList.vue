<template>
  <div class="fill-height d-flex flex-column">
    <!-- 工具栏 -->
    <v-toolbar flat color="surface" border="b" class="flex-grow-0 px-2">
      <v-toolbar-title class="text-subtitle-1 font-weight-bold">
        {{ currentCategoryLabel }}
        <v-chip size="x-small" class="ml-1" color="primary" variant="tonal">
          {{ newsStore.newsList.length }}
        </v-chip>
      </v-toolbar-title>

      <v-spacer />

      <!-- 模型选择 -->
      <ModelSelector v-model="selectedModel" class="mr-2" />

      <!-- 一键分析 -->
      <v-btn
        size="small"
        variant="tonal"
        color="secondary"
        class="mr-2"
        :loading="analyzingCategory"
        :disabled="!selectedModel || !newsStore.newsList.length"
        @click="handleAnalyzeCategory"
      >
        <v-icon start size="15">mdi-layers-outline</v-icon>
        <span class="d-none d-sm-inline">一键分析</span>
      </v-btn>

      <!-- 刷新新闻 -->
      <v-btn
        size="small"
        variant="elevated"
        color="primary"
        class="mr-2"
        :loading="newsStore.refreshStatus.status === 'refreshing'"
        @click="newsStore.triggerRefresh()"
      >
        <v-icon start size="15">mdi-refresh</v-icon>
        <span class="d-none d-sm-inline">刷新新闻</span>
      </v-btn>

      <!-- 导出菜单 -->
      <v-menu>
        <template #activator="{ props: menuProps }">
          <v-btn v-bind="menuProps" variant="text" size="small" icon>
            <v-icon>mdi-download-outline</v-icon>
          </v-btn>
        </template>
        <v-list density="compact" min-width="140">
          <v-list-item
            prepend-icon="mdi-code-json"
            title="导出 JSON"
            @click="newsStore.doExport('json')"
          />
          <v-list-item
            prepend-icon="mdi-language-html5"
            title="导出 HTML"
            @click="newsStore.doExport('html')"
          />
        </v-list>
      </v-menu>
    </v-toolbar>

    <!-- 刷新进度条 -->
    <v-progress-linear
      v-if="newsStore.refreshStatus.status === 'refreshing'"
      :model-value="refreshPercent"
      color="primary"
      height="3"
      class="flex-grow-0"
    />

    <!-- 刷新完成提示 -->
    <v-alert
      v-if="newsStore.refreshStatus.status === 'idle' && newsStore.refreshStatus.last_refresh && justRefreshed"
      type="success"
      density="compact"
      variant="tonal"
      closable
      class="mx-4 mt-3 flex-grow-0"
      @click:close="justRefreshed = false"
    >
      刷新完成，新增 {{ newsStore.refreshStatus.added }} 条新闻
    </v-alert>

    <!-- 加载状态 -->
    <div
      v-if="newsStore.loading"
      class="d-flex justify-center align-center flex-grow-1"
    >
      <v-progress-circular indeterminate color="primary" size="52" />
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="!newsStore.newsList.length"
      class="d-flex flex-column align-center justify-center flex-grow-1 text-medium-emphasis"
    >
      <v-icon size="72" class="mb-4" color="grey-lighten-2">mdi-newspaper-variant-outline</v-icon>
      <p class="text-body-1">暂无新闻</p>
      <p class="text-caption">点击"刷新新闻"从订阅源获取最新内容</p>
      <v-btn
        color="primary"
        variant="tonal"
        class="mt-4"
        :loading="newsStore.refreshStatus.status === 'refreshing'"
        @click="newsStore.triggerRefresh()"
      >
        <v-icon start>mdi-refresh</v-icon>立即刷新
      </v-btn>
    </div>

    <!-- 新闻卡片网格 -->
    <div v-else class="flex-grow-1 overflow-y-auto">
      <v-container fluid class="pa-4">
        <v-row>
          <v-col
            v-for="news in newsStore.newsList"
            :key="news.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
            xl="2"
          >
            <NewsCard
              :news="news"
              :analyzing="analyzingId === news.id"
              :tweeting="tweetingId === news.id"
              @analyze="handleAnalyze"
              @tweet="handleTweet"
            />
          </v-col>
        </v-row>
      </v-container>
    </div>

    <!-- LLM 结果弹窗 -->
    <LlmResult
      v-model="showResult"
      :title="resultTitle"
      :content="resultContent"
      :loading="resultLoading"
      :error="resultError"
      :is-tweet="isTweetMode"
      :news-link="resultNewsLink"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useNewsStore } from '../stores/newsStore'
import NewsCard      from './NewsCard.vue'
import ModelSelector from './ModelSelector.vue'
import LlmResult     from './LlmResult.vue'
import { analyzeNews, analyzeCategory, generateTweet } from '../api/index'

const newsStore = useNewsStore()

// ── 模型选择 ─────────────────────────────────
const selectedModel = ref('')

// ── 类别标签 ─────────────────────────────────
const currentCategoryLabel = computed(() => {
  const c = newsStore.currentCategory
  return c === 'all' ? '全部新闻' : c
})

// ── 刷新进度 ─────────────────────────────────
const justRefreshed = ref(false)
const refreshPercent = computed(() => {
  const { total, done } = newsStore.refreshStatus
  if (!total) return 0
  return Math.round((done / total) * 100)
})

watch(
  () => newsStore.refreshStatus.status,
  (val) => { if (val === 'idle' && newsStore.refreshStatus.last_refresh) justRefreshed.value = true }
)

// ── 操作状态 ─────────────────────────────────
const analyzingId       = ref(null)
const tweetingId        = ref(null)
const analyzingCategory = ref(false)

// ── LLM 弹窗 ─────────────────────────────────
const showResult    = ref(false)
const resultTitle   = ref('')
const resultContent = ref('')
const resultLoading = ref(false)
const resultError   = ref('')
const isTweetMode   = ref(false)
const resultNewsLink = ref('')   // 原文链接，单条新闻时填入

function openResult(title, isTweet = false, newsLink = '') {
  resultTitle.value    = title
  resultContent.value  = ''
  resultError.value    = ''
  resultLoading.value  = true
  isTweetMode.value    = isTweet
  resultNewsLink.value = newsLink
  showResult.value     = true
}

// ── 单条新闻分析 ─────────────────────────────
async function handleAnalyze(news) {
  if (!selectedModel.value) return
  analyzingId.value = news.id
  openResult(`分析：${news.title}`, false, news.link)
  try {
    const { data } = await analyzeNews({ news_id: news.id, model_name: selectedModel.value })
    resultContent.value = data.result
  } catch (e) {
    resultError.value = e.message
  } finally {
    resultLoading.value = false
    analyzingId.value   = null
  }
}

// ── 生成推文 ─────────────────────────────────
async function handleTweet(news) {
  if (!selectedModel.value) return
  tweetingId.value = news.id
  openResult(`推文：${news.title}`, true, news.link)
  try {
    const { data } = await generateTweet({ news_id: news.id, model_name: selectedModel.value })
    resultContent.value = data.result
  } catch (e) {
    resultError.value = e.message
  } finally {
    resultLoading.value = false
    tweetingId.value    = null
  }
}

// ── 一键分析类别 ─────────────────────────────
async function handleAnalyzeCategory() {
  if (!selectedModel.value) return
  analyzingCategory.value = true
  // 直接传当前类别（'all' 时后端查全部新闻，不再强制映射为'综合'）
  const cat = newsStore.currentCategory
  openResult(`类别总结：${currentCategoryLabel.value}`)   // 类别分析无原文链接
  try {
    const { data } = await analyzeCategory({ category: cat, model_name: selectedModel.value })
    resultContent.value = data.result
  } catch (e) {
    resultError.value = e.message
  } finally {
    resultLoading.value     = false
    analyzingCategory.value = false
  }
}
</script>
