<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="480"
  >
    <v-card rounded="xl" elevation="8">
      <!-- 渐变标题栏 -->
      <div class="share-header pa-5 d-flex align-center">
        <div class="share-icon-wrap mr-3">
          <v-icon color="white" size="22">mdi-share-variant</v-icon>
        </div>
        <div>
          <div class="text-subtitle-1 font-weight-bold text-white">分享内容</div>
          <div class="text-caption" style="color: rgba(255,255,255,0.75);">选择平台一键发布</div>
        </div>
        <v-spacer />
        <v-btn
          icon
          size="small"
          variant="text"
          style="color: rgba(255,255,255,0.85);"
          @click="$emit('update:modelValue', false)"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </div>

      <v-card-text class="pa-5">
        <!-- 内容预览区 -->
        <div class="preview-box pa-3 mb-4 rounded-lg">
          <div class="d-flex align-center mb-2">
            <v-icon size="14" color="grey-darken-1" class="mr-1">mdi-text-box-outline</v-icon>
            <span class="text-caption text-medium-emphasis">内容预览</span>
            <v-spacer />
            <span class="text-caption text-medium-emphasis">{{ plainText.length }} 字</span>
          </div>
          <div class="preview-text">{{ previewText }}</div>
        </div>

        <!-- 说明文字 -->
        <div class="d-flex align-center mb-3 gap-1">
          <v-icon size="14" color="primary">mdi-information-outline</v-icon>
          <span class="text-caption text-medium-emphasis">
            点击平台卡片，内容将自动复制并跳转至对应发布页
          </span>
        </div>

        <!-- 平台卡片横排 -->
        <div class="d-flex gap-3 mb-1">
          <!-- 微博 -->
          <div class="platform-card flex-1" @click="shareWeibo">
            <div class="platform-icon-wrap" style="background: linear-gradient(135deg, #FF4C6B, #E6162D);">
              <v-icon color="white" size="26">mdi-sina-weibo</v-icon>
            </div>
            <div class="platform-name">微博</div>
            <v-chip size="x-small" color="success" variant="flat" class="platform-badge">
              直接预填
            </v-chip>
          </div>

          <!-- 小红书 -->
          <div class="platform-card flex-1" @click="shareXHS">
            <div class="platform-icon-wrap" style="background: linear-gradient(135deg, #FF6B8A, #FF2442);">
              <v-icon color="white" size="26">mdi-notebook-heart-outline</v-icon>
            </div>
            <div class="platform-name">小红书</div>
            <v-chip size="x-small" color="orange" variant="flat" class="platform-badge">
              复制粘贴
            </v-chip>
          </div>

          <!-- 微信公众号 -->
          <div class="platform-card flex-1" @click="shareWechat">
            <div class="platform-icon-wrap" style="background: linear-gradient(135deg, #3ECFA0, #07C160);">
              <v-icon color="white" size="26">mdi-wechat</v-icon>
            </div>
            <div class="platform-name">公众号</div>
            <v-chip size="x-small" color="orange" variant="flat" class="platform-badge">
              复制粘贴
            </v-chip>
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <!-- 底部操作 -->
      <v-card-actions class="px-5 py-3">
        <v-btn
          variant="tonal"
          size="small"
          rounded="lg"
          :color="copied ? 'success' : 'grey-darken-1'"
          prepend-icon="mdi-content-copy"
          @click="copyOnly"
        >
          <v-icon start size="15">{{ copied ? 'mdi-check-circle' : 'mdi-content-copy' }}</v-icon>
          {{ copied ? '已复制' : '仅复制' }}
        </v-btn>
        <v-spacer />
        <v-btn variant="text" size="small" @click="$emit('update:modelValue', false)">
          关闭
        </v-btn>
      </v-card-actions>
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

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  content:    { type: String,  default: '' },
})

defineEmits(['update:modelValue'])

const copied = ref(false)
const snack  = ref({ show: false, text: '', color: 'success', icon: 'mdi-check-circle' })

/** Markdown → 纯文本 */
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

/** 预览文字：最多 80 字，超出省略 */
const previewText = computed(() => {
  const t = plainText.value
  return t.length > 80 ? t.slice(0, 80) + '…' : t
})

function showSnack(text, color = 'success') {
  const icons = { success: 'mdi-check-circle', info: 'mdi-rocket-launch-outline', warning: 'mdi-content-paste' }
  snack.value = { show: true, text, color, icon: icons[color] || 'mdi-information' }
}

async function copyText() {
  try {
    await navigator.clipboard.writeText(plainText.value)
  } catch {
    const el = document.createElement('textarea')
    el.value = plainText.value
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
}

async function copyOnly() {
  await copyText()
  copied.value = true
  showSnack('内容已复制到剪贴板')
  setTimeout(() => (copied.value = false), 2500)
}

function shareWeibo() {
  const url = `https://service.weibo.com/share/share.php?title=${encodeURIComponent(plainText.value)}&appkey=`
  window.open(url, '_blank', 'noopener,noreferrer')
  showSnack('已跳转微博，内容已预填', 'info')
}

async function shareXHS() {
  await copyText()
  window.open('https://creator.xiaohongshu.com/publish/publish', '_blank', 'noopener,noreferrer')
  showSnack('已复制，请在小红书粘贴发布', 'warning')
}

async function shareWechat() {
  await copyText()
  window.open('https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77', '_blank', 'noopener,noreferrer')
  showSnack('已复制，请在公众号编辑器粘贴', 'warning')
}
</script>

<style scoped>
/* 渐变标题栏 */
.share-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 12px 0 0;
}

.share-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 内容预览框 */
.preview-box {
  background: #f8f9fc;
  border: 1px solid #e8eaf0;
}

.preview-text {
  font-size: 0.83rem;
  color: rgba(0, 0, 0, 0.7);
  line-height: 1.6;
  white-space: pre-line;
  word-break: break-all;
}

/* 平台卡片 */
.platform-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px 14px;
  border-radius: 14px;
  border: 1.5px solid #eef0f6;
  background: #fff;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  user-select: none;
}

.platform-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #d0d4e8;
}

.platform-card:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.platform-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

.platform-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.75);
}

.platform-badge {
  font-size: 0.68rem !important;
}

.flex-1 {
  flex: 1;
}
</style>
