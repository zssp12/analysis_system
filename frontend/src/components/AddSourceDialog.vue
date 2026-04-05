<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="540"
    persistent
  >
    <v-card rounded="lg">
      <v-card-title class="pa-4 d-flex align-center">
        <v-icon start color="primary">mdi-rss-box</v-icon>
        添加订阅源
        <v-spacer />
        <v-btn icon size="small" @click="handleClose">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <v-form ref="formRef" v-model="valid" lazy-validation>
          <!-- 名称 -->
          <v-text-field
            v-model="form.name"
            label="订阅源名称"
            placeholder="例：TechCrunch"
            :rules="[(v) => !!v?.trim() || '名称不能为空']"
            variant="outlined"
            density="compact"
            class="mb-3"
            autofocus
          />

          <!-- URL -->
          <v-text-field
            v-model="form.url"
            label="URL 地址"
            placeholder="https://example.com/feed 或 https://news.example.edu.cn"
            :rules="[
              (v) => !!v?.trim() || 'URL 不能为空',
              (v) => isValidUrl(v) || '请输入有效的 http/https URL',
            ]"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <!-- 类型 -->
          <v-btn-toggle
            v-model="form.type"
            mandatory
            density="compact"
            color="primary"
            class="mb-3 w-100"
            style="width:100%"
          >
            <v-btn value="rss" style="flex:1">
              <v-icon start size="16">mdi-rss</v-icon>RSS 订阅
            </v-btn>
            <v-btn value="crawler" style="flex:1">
              <v-icon start size="16">mdi-spider-web</v-icon>网页爬虫
            </v-btn>
          </v-btn-toggle>

          <!-- 类别 -->
          <v-select
            v-model="form.category"
            :items="CATEGORIES"
            label="所属类别"
            :rules="[(v) => !!v || '请选择类别']"
            variant="outlined"
            density="compact"
          />
        </v-form>

        <!-- 提示信息 -->
        <v-alert
          v-if="errorMsg"
          type="error"
          variant="tonal"
          density="compact"
          rounded="lg"
          class="mt-3"
        >
          {{ errorMsg }}
        </v-alert>
        <v-alert
          v-if="successMsg"
          type="success"
          variant="tonal"
          density="compact"
          rounded="lg"
          class="mt-3"
        >
          {{ successMsg }}
        </v-alert>

        <!-- 校验进度提示 -->
        <div v-if="submitting" class="d-flex align-center gap-2 mt-3 text-medium-emphasis text-body-2">
          <v-progress-circular indeterminate size="16" width="2" color="primary" />
          正在校验 URL 有效性，这可能需要几秒钟…
        </div>
      </v-card-text>

      <v-card-actions class="pa-3">
        <v-spacer />
        <v-btn variant="text" :disabled="submitting" @click="handleClose">取消</v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          :loading="submitting"
          :disabled="!valid"
          @click="submit"
        >
          添加
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSourceStore } from '../stores/sourceStore'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit  = defineEmits(['update:modelValue', 'added'])

const sourceStore = useSourceStore()

const CATEGORIES = ['科技', '体育', '财经', '高校资讯', '综合', '娱乐', '国际', '社会']

const formRef    = ref(null)
const valid      = ref(false)
const submitting = ref(false)
const errorMsg   = ref('')
const successMsg = ref('')

const form = ref({ name: '', url: '', type: 'rss', category: '科技' })

function isValidUrl(v) {
  try {
    const u = new URL(v)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

function handleClose() {
  if (submitting.value) return
  emit('update:modelValue', false)
}

// 关闭时重置表单
watch(() => props.modelValue, (val) => {
  if (!val) {
    setTimeout(() => {
      formRef.value?.reset()
      form.value = { name: '', url: '', type: 'rss', category: '科技' }
      errorMsg.value = ''
      successMsg.value = ''
    }, 300)
  }
})

async function submit() {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  submitting.value = true
  errorMsg.value   = ''
  successMsg.value = ''

  try {
    await sourceStore.addSource({ ...form.value })
    successMsg.value = `"${form.value.name}" 添加成功！`
    setTimeout(() => {
      emit('update:modelValue', false)
      emit('added')
    }, 1200)
  } catch (e) {
    errorMsg.value = e.message || '添加失败，请检查 URL 是否可访问'
  } finally {
    submitting.value = false
  }
}
</script>
