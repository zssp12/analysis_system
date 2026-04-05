<template>
  <v-card
    elevation="2"
    rounded="lg"
    class="news-card d-flex flex-column"
    height="100%"
  >
    <!-- 缩略图 -->
    <v-img
      v-if="news.thumbnail"
      :src="news.thumbnail"
      height="160"
      cover
      class="flex-grow-0"
    >
      <template #error>
        <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
          <v-icon size="40" color="grey-lighten-1">mdi-image-broken</v-icon>
        </div>
      </template>
      <!-- 类别标签浮层 -->
      <v-chip
        size="x-small"
        class="ma-2"
        color="primary"
        style="position:absolute;top:0;right:0;"
      >
        {{ news.category }}
      </v-chip>
    </v-img>

    <!-- 无缩略图时的类别标签 -->
    <div v-else class="px-3 pt-3">
      <v-chip size="x-small" color="primary" variant="tonal">{{ news.category }}</v-chip>
    </div>

    <!-- 标题 -->
    <v-card-title class="pb-1 pt-2 news-title">
      <a
        :href="news.link"
        target="_blank"
        rel="noopener noreferrer"
        class="text-decoration-none text-on-surface"
      >
        {{ news.title }}
      </a>
    </v-card-title>

    <!-- 时间 -->
    <v-card-subtitle class="pb-1 d-flex align-center gap-1">
      <v-icon size="13" color="medium-emphasis">mdi-clock-outline</v-icon>
      <span>{{ formatDate(news.published_at) }}</span>
    </v-card-subtitle>

    <!-- 描述 -->
    <v-card-text class="py-1 text-body-2 text-medium-emphasis flex-grow-1">
      <span v-if="!expanded">
        {{ truncatedDesc }}
        <a
          v-if="needsExpand"
          href="#"
          class="text-primary text-decoration-none"
          @click.prevent="expanded = true"
        >阅读更多</a>
      </span>
      <span v-else>
        {{ news.description }}
        <a href="#" class="text-primary text-decoration-none" @click.prevent="expanded = false">
          收起
        </a>
      </span>
    </v-card-text>

    <!-- 操作按钮 -->
    <v-card-actions class="pt-0 px-3 pb-2">
      <v-btn
        size="small"
        variant="tonal"
        color="primary"
        :loading="analyzing"
        @click="$emit('analyze', news)"
      >
        <v-icon start size="15">mdi-brain</v-icon>分析
      </v-btn>
      <v-btn
        size="small"
        variant="tonal"
        color="secondary"
        :loading="tweeting"
        @click="$emit('tweet', news)"
      >
        <v-icon start size="15">mdi-send-outline</v-icon>推文
      </v-btn>
      <v-spacer />
      <!-- 外链按钮：用 tag="a" 避免 v-btn href 焦点残留 -->
      <v-btn
        size="small"
        variant="text"
        density="compact"
        icon="mdi-open-in-new"
        tag="a"
        :href="news.link"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="在新标签页打开"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  news:      { type: Object, required: true },
  analyzing: { type: Boolean, default: false },
  tweeting:  { type: Boolean, default: false },
})

defineEmits(['analyze', 'tweet'])

const expanded = ref(false)
const MAX_LEN  = 120

const truncatedDesc = computed(() => {
  const desc = props.news.description || ''
  return desc.length > MAX_LEN ? desc.slice(0, MAX_LEN) + '…' : desc
})

const needsExpand = computed(() =>
  (props.news.description || '').length > MAX_LEN
)

function formatDate(dt) {
  if (!dt) return '未知时间'
  const d = new Date(dt)
  return d.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.news-card {
  transition: box-shadow 0.2s ease;
}
.news-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
}
.news-title {
  font-size: 0.92rem !important;
  line-height: 1.4 !important;
  font-weight: 600;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.news-title a {
  color: inherit;
}
.news-title a:hover {
  color: rgb(var(--v-theme-primary));
}
</style>
