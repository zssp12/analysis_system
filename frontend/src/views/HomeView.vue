<template>
  <v-app :theme="theme">
    <!-- 顶部导航栏 -->
    <v-app-bar elevation="2" color="primary">
      <v-app-bar-nav-icon @click="drawer = !drawer" />

      <v-app-bar-title class="d-flex align-center gap-2">
        <v-icon class="mr-1">mdi-newspaper-variant-multiple</v-icon>
        <span class="font-weight-bold">新闻聚合与推送系统</span>
      </v-app-bar-title>

      <template #append>
        <!-- 刷新状态指示 -->
        <v-chip
          v-if="newsStore.refreshStatus.status === 'refreshing'"
          color="warning"
          size="small"
          class="mr-2"
        >
          <v-progress-circular size="12" width="2" indeterminate class="mr-1" />
          正在刷新（{{ newsStore.refreshStatus.done }}/{{ newsStore.refreshStatus.total }}）
        </v-chip>
        <v-chip
          v-else-if="newsStore.refreshStatus.last_refresh"
          variant="tonal"
          size="small"
          class="mr-2"
        >
          <v-icon start size="14">mdi-clock-check-outline</v-icon>
          {{ formatLastRefresh }}
        </v-chip>

        <!-- 暗/亮模式切换 -->
        <v-btn
          :icon="theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          variant="text"
          class="mr-1"
          @click="toggleTheme"
        />
      </template>
    </v-app-bar>

    <!-- 左侧类别侧栏 -->
    <CategorySidebar v-model="drawer" @add-source="addSourceDialog = true" />

    <!-- 主内容区 -->
    <v-main class="bg-grey-lighten-5">
      <div class="fill-height">
        <NewsCardList />
      </div>
    </v-main>

    <!-- 添加订阅源弹窗 -->
    <AddSourceDialog
      v-model="addSourceDialog"
      @added="onSourceAdded"
    />

    <!-- 全局 Snackbar 通知 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3500"
      location="bottom right"
      rounded="lg"
    >
      <v-icon start size="18">{{ snackbar.icon }}</v-icon>
      {{ snackbar.text }}
      <template #actions>
        <v-btn icon size="x-small" @click="snackbar.show = false">
          <v-icon size="16">mdi-close</v-icon>
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNewsStore }   from '../stores/newsStore'
import { useSourceStore } from '../stores/sourceStore'
import CategorySidebar  from '../components/CategorySidebar.vue'
import NewsCardList     from '../components/NewsCardList.vue'
import AddSourceDialog  from '../components/AddSourceDialog.vue'

const newsStore   = useNewsStore()
const sourceStore = useSourceStore()

// ── 主题切换 ─────────────────────────────────
const theme = ref('light')
function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
}

// ── 侧栏控制 ─────────────────────────────────
const drawer          = ref(true)
const addSourceDialog = ref(false)

// ── 刷新时间格式化 ────────────────────────────
const formatLastRefresh = computed(() => {
  const t = newsStore.refreshStatus.last_refresh
  if (!t) return ''
  return new Date(t).toLocaleTimeString('zh-CN', {
    hour:   '2-digit',
    minute: '2-digit',
  })
})

// ── Snackbar ─────────────────────────────────
const snackbar = ref({ show: false, text: '', color: 'success', icon: 'mdi-check-circle' })

function showSnackbar(text, color = 'success') {
  const icons = {
    success: 'mdi-check-circle',
    error:   'mdi-alert-circle',
    info:    'mdi-information',
    warning: 'mdi-alert',
  }
  snackbar.value = { show: true, text, color, icon: icons[color] || 'mdi-information' }
}

// ── 添加订阅源回调 ────────────────────────────
async function onSourceAdded() {
  showSnackbar('订阅源添加成功！')
  await sourceStore.fetchSources()
}

// ── 初始化 ────────────────────────────────────
onMounted(async () => {
  await Promise.all([
    newsStore.fetchNews('all'),
    newsStore.fetchCategories(),
    newsStore.fetchCounts(),
    sourceStore.fetchSources(),
  ])
  if (!newsStore.newsList.length) {
    // 首次打开自动刷新
    showSnackbar('正在后台拉取最新新闻…', 'info')
    newsStore.triggerRefresh()
  }
})
</script>
