<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="720"
    scrollable
  >
    <v-card rounded="lg" class="llm-result-card">
      <!-- 标题栏 -->
      <v-card-title class="pa-4 d-flex align-center">
        <v-icon start :color="isTweet ? 'secondary' : 'primary'">
          {{ isTweet ? 'mdi-send-outline' : 'mdi-brain' }}
        </v-icon>
        <span class="text-truncate flex-grow-1" style="max-width:500px">{{ title }}</span>
        <v-spacer />
        <v-btn icon size="small" @click="$emit('update:modelValue', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <!-- 内容区 -->
      <v-card-text class="pa-5" style="max-height: 60vh; overflow-y: auto;">
        <!-- 加载中 -->
        <div v-if="loading" class="d-flex flex-column align-center justify-center py-12 gap-4">
          <v-progress-circular indeterminate color="primary" size="52" />
          <span class="text-medium-emphasis">大模型思考中，请稍候…</span>
        </div>

        <!-- 错误 -->
        <v-alert v-else-if="error" type="error" variant="tonal" rounded="lg">
          {{ error }}
        </v-alert>

        <!-- Markdown 结果 -->
        <div
          v-else
          class="markdown-body"
          v-html="renderedContent"
        />
      </v-card-text>

      <v-divider />

      <!-- 底部操作 -->
      <v-card-actions class="pa-3">
        <v-btn
          variant="tonal"
          size="small"
          :color="copied ? 'success' : 'default'"
          :disabled="loading || !!error || !content"
          @click="copyToClipboard"
        >
          <v-icon start size="16">{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
          {{ copied ? '已复制' : '复制内容' }}
        </v-btn>

        <!-- 分享推送按钮（toggle 折叠面板） -->
        <v-btn
          v-if="!loading && !error && content"
          variant="tonal"
          size="small"
          color="secondary"
          class="ml-2"
          @click="shareMenuOpen = !shareMenuOpen"
        >
          <v-icon start size="16">mdi-share-variant</v-icon>
          分享推送
          <v-icon end size="14">
            {{ shareMenuOpen ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
          </v-icon>
        </v-btn>

        <!-- 查看原文按钮：有链接时显示 -->
        <v-btn
          v-if="newsLink"
          variant="tonal"
          size="small"
          color="primary"
          class="ml-2"
          :href="newsLink"
          target="_blank"
          rel="noopener noreferrer"
        >
          <v-icon start size="16">mdi-open-in-new</v-icon>
          查看原文
        </v-btn>

        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">关闭</v-btn>
      </v-card-actions>

      <!-- 分享平台折叠面板（向下展开，紧贴底部操作栏） -->
      <v-expand-transition>
        <div v-if="shareMenuOpen" class="share-panel">
          <v-divider />
          <div class="share-panel-header px-4 py-2 d-flex align-center">
            <v-icon size="14" color="secondary" class="mr-1">mdi-rocket-launch-outline</v-icon>
            <span class="text-caption font-weight-bold text-secondary">选择分享平台</span>
          </div>
          <div class="px-3 pb-3 d-flex flex-column gap-1">
            <!-- 微博 -->
            <div class="share-item" @click="shareWeibo">
              <div class="share-item-icon" style="background: linear-gradient(135deg,#FF4C6B,#E6162D);">
                <v-icon color="white" size="18">mdi-sina-weibo</v-icon>
              </div>
              <div class="share-item-body">
                <div class="share-item-name">微博</div>
                <div class="share-item-desc">内容自动预填到微博发布框</div>
              </div>
              <v-chip size="x-small" color="success" variant="flat" class="share-badge">直接预填</v-chip>
            </div>

            <!-- 小红书 -->
            <div class="share-item" @click="shareXHS">
              <div class="share-item-icon" style="background: linear-gradient(135deg,#FF6B8A,#FF2442);">
                <v-icon color="white" size="18">mdi-notebook-heart-outline</v-icon>
              </div>
              <div class="share-item-body">
                <div class="share-item-name">小红书</div>
                <div class="share-item-desc">自动复制内容，跳转创作者发布页</div>
              </div>
              <v-chip size="x-small" color="orange" variant="flat" class="share-badge">复制粘贴</v-chip>
            </div>

            <!-- 微信公众号 -->
            <div class="share-item" @click="shareWechat">
              <div class="share-item-icon" style="background: linear-gradient(135deg,#3ECFA0,#07C160);">
                <v-icon color="white" size="18">mdi-wechat</v-icon>
              </div>
              <div class="share-item-body">
                <div class="share-item-name">微信公众号</div>
                <div class="share-item-desc">自动复制内容，跳转公众号编辑器</div>
              </div>
              <v-chip size="x-small" color="orange" variant="flat" class="share-badge">复制粘贴</v-chip>
            </div>
          </div>
        </div>
      </v-expand-transition>
    </v-card>
  </v-dialog>

  <!-- 操作反馈 Snackbar -->
  <v-snackbar
    v-model="snack.show"
    :color="snack.color"
    :timeout="2500"
    location="bottom right"
    rounded="lg"
    min-width="0"
  >
    <div class="d-flex align-center gap-2">
      <v-icon size="18">{{ snack.icon }}</v-icon>
      {{ snack.text }}
    </div>
  </v-snackbar>
</template>

<script setup>
import { ref, computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html:        false,
  linkify:     true,
  typographer: true,
  breaks:      true,
})

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '分析结果' },
  content:    { type: String,  default: '' },
  loading:    { type: Boolean, default: false },
  error:      { type: String,  default: '' },
  isTweet:    { type: Boolean, default: false },
  newsLink:   { type: String,  default: '' },
})

defineEmits(['update:modelValue'])

const copied        = ref(false)
const shareMenuOpen = ref(false)
const snack         = ref({ show: false, text: '', color: 'success', icon: 'mdi-check-circle' })

const renderedContent = computed(() => {
  if (!props.content) return '<p class="text-medium-emphasis">（暂无内容）</p>'
  return md.render(props.content)
})

/** Markdown → 纯文本（社交平台粘贴用） */
const plainText = computed(() =>
  props.content
    .replace(/#{1,6}\s+/g, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')
    .replace(/^\s*[-*+]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
)

function showSnack(text, color = 'success') {
  const icons = { success: 'mdi-check-circle', info: 'mdi-rocket-launch-outline', warning: 'mdi-content-paste' }
  snack.value = { show: true, text, color, icon: icons[color] || 'mdi-information' }
}

async function _writeClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const el = document.createElement('textarea')
    el.value = text
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
}

async function copyToClipboard() {
  await _writeClipboard(props.content || '')
  copied.value = true
  setTimeout(() => (copied.value = false), 2500)
}

/** 微博：官方分享 URL，内容直接预填 */
function shareWeibo() {
  const url = `https://service.weibo.com/share/share.php?title=${encodeURIComponent(plainText.value)}&appkey=`
  window.open(url, '_blank', 'noopener,noreferrer')
  shareMenuOpen.value = false
  showSnack('已跳转微博，内容已预填', 'info')
}

/** 小红书：复制纯文本 + 跳转创作者发布页 */
async function shareXHS() {
  await _writeClipboard(plainText.value)
  window.open('https://creator.xiaohongshu.com/publish/publish', '_blank', 'noopener,noreferrer')
  shareMenuOpen.value = false
  showSnack('已复制，请在小红书发布页粘贴', 'warning')
}

/** 微信公众号：复制纯文本 + 跳转图文编辑页 */
async function shareWechat() {
  await _writeClipboard(plainText.value)
  window.open('https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77', '_blank', 'noopener,noreferrer')
  shareMenuOpen.value = false
  showSnack('已复制，请在公众号编辑器粘贴', 'warning')
}
</script>

<style scoped>
/* ── Markdown 渲染区 ── */
.llm-result-card {
  position: relative;
  overflow: visible;
}
.markdown-body {
  line-height: 1.75;
  font-size: 0.93rem;
  color: rgba(0, 0, 0, 0.87);
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 1.2em 0 0.6em;
  font-weight: 700;
  line-height: 1.3;
}
.markdown-body :deep(h1) { font-size: 1.4rem; }
.markdown-body :deep(h2) { font-size: 1.2rem; }
.markdown-body :deep(h3) { font-size: 1.05rem; }
.markdown-body :deep(p)  { margin-bottom: 0.9em; }
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 0.9em;
}
.markdown-body :deep(li) { margin-bottom: 0.3em; }
.markdown-body :deep(code) {
  background: #f3f4f6;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.87em;
  font-family: 'Consolas', monospace;
}
.markdown-body :deep(pre) {
  background: #f3f4f6;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 0.9em;
}
.markdown-body :deep(blockquote) {
  border-left: 4px solid #1565C0;
  padding: 4px 16px;
  margin: 0.9em 0;
  color: rgba(0, 0, 0, 0.6);
  background: #f0f4ff;
  border-radius: 0 6px 6px 0;
}
.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(a) { color: #1565C0; }
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 1.2em 0;
}

/* ── 分享下拉面板 ── */
.share-panel {
  background: #fafbff;
}
.share-panel-header {
  background: #fafbff;
}

/* ── 分享列表项 ── */
.share-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.share-item:hover {
  background: rgba(0, 0, 0, 0.04);
}
.share-item:active {
  background: rgba(0, 0, 0, 0.08);
}
.share-item-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}
.share-item-body {
  flex: 1;
  min-width: 0;
}
.share-item-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.3;
}
.share-item-desc {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.share-badge {
  flex-shrink: 0;
  font-size: 0.68rem !important;
}
</style>
