<template>
  <v-navigation-drawer
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    width="240"
    border="r"
  >
    <!-- 品牌标题 -->
    <v-list-item
      prepend-icon="mdi-newspaper-variant"
      title="新闻聚合系统"
      subtitle="AI 驱动的内容平台"
      class="py-4 bg-primary"
      base-color="white"
    />

    <v-divider />

    <!-- 类别列表 -->
    <v-list
      :selected="[newsStore.currentCategory]"
      density="compact"
      nav
      class="mt-1"
      @update:selected="(v) => v.length && selectCategory(v[0])"
    >
      <v-list-subheader>新闻类别</v-list-subheader>
      <v-list-item
        v-for="cat in newsStore.categories"
        :key="cat"
        :value="cat"
        :prepend-icon="categoryIcon(cat)"
        :title="cat === 'all' ? '全部新闻' : cat"
        active-color="primary"
        rounded="lg"
        class="mb-1"
      >
        <template #append>
          <v-badge
            v-if="countByCategory(cat) > 0"
            :content="countByCategory(cat)"
            color="primary"
            inline
          />
        </template>
      </v-list-item>
    </v-list>

    <v-divider class="mt-2" />

    <!-- 订阅源管理 -->
    <v-list density="compact" nav class="mt-1">
      <v-list-subheader>订阅源管理</v-list-subheader>
      <v-list-item
        prepend-icon="mdi-rss-box"
        title="添加订阅源"
        rounded="lg"
        @click="$emit('add-source')"
      />
      <v-list-item
        prepend-icon="mdi-cog-outline"
        title="管理订阅源"
        rounded="lg"
        @click="showSources = true"
      />
    </v-list>

    <!-- 订阅源列表弹窗 -->
    <v-dialog v-model="showSources" max-width="600" scrollable>
      <v-card>
        <v-card-title class="pa-4 d-flex align-center">
          <v-icon start>mdi-rss</v-icon>订阅源列表
          <v-spacer />
          <v-btn icon size="small" @click="showSources = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0" style="max-height: 480px;">
          <v-list lines="two">
            <v-list-item
              v-for="src in sourceStore.sources"
              :key="src.id"
              :subtitle="src.url"
            >
              <template #title>
                <span :class="{ 'text-disabled': !src.enabled }">{{ src.name }}</span>
                <v-chip size="x-small" class="ml-2" :color="src.type === 'rss' ? 'info' : 'warning'">
                  {{ src.type }}
                </v-chip>
                <v-chip size="x-small" class="ml-1" color="secondary" variant="tonal">
                  {{ src.category }}
                </v-chip>
              </template>
              <template #append>
                <v-switch
                  :model-value="src.enabled"
                  density="compact"
                  hide-details
                  color="primary"
                  class="mr-2"
                  @change="sourceStore.toggle(src.id)"
                />
                <v-btn icon size="x-small" color="error" variant="text" @click="removeSource(src.id)">
                  <v-icon size="18">mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
          <div v-if="!sourceStore.sources.length" class="pa-8 text-center text-disabled">
            暂无订阅源
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-navigation-drawer>
</template>

<script setup>
import { ref } from 'vue'
import { useNewsStore } from '../stores/newsStore'
import { useSourceStore } from '../stores/sourceStore'

defineProps({ modelValue: { type: Boolean, default: true } })
defineEmits(['update:modelValue', 'add-source'])

const newsStore   = useNewsStore()
const sourceStore = useSourceStore()
const showSources = ref(false)

const CATEGORY_ICONS = {
  all:      'mdi-view-dashboard-outline',
  科技:     'mdi-cpu-64-bit',
  国际:     'mdi-earth',
  财经:     'mdi-chart-line',
  体育:     'mdi-soccer',
  娱乐:     'mdi-music-note',
  科学:     'mdi-flask-outline',
  健康:     'mdi-heart-pulse',
  高校资讯: 'mdi-school-outline',
  综合:     'mdi-newspaper',
  军事:     'mdi-shield-outline',
  经济:     'mdi-trending-up',
}

function categoryIcon(cat) {
  return CATEGORY_ICONS[cat] || 'mdi-folder-outline'
}

function countByCategory(cat) {
  // 使用后端统计的准确数量，不依赖当前页面加载的 newsList
  return newsStore.countMap[cat] || 0
}

function selectCategory(cat) {
  newsStore.fetchNews(cat)
}

async function removeSource(id) {
  await sourceStore.removeSource(id)
}
</script>
