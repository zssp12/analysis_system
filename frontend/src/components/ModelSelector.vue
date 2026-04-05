<template>
  <!-- 模型选择下拉框 -->
  <v-select
    v-model="selected"
    :items="models"
    item-title="display"
    item-value="name"
    label="选择模型"
    density="compact"
    variant="outlined"
    hide-details
    :loading="loading"
    :no-data-text="error || '未配置任何模型'"
    style="min-width: 160px; max-width: 220px;"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #prepend-inner>
      <v-icon size="16" color="primary">mdi-robot-outline</v-icon>
    </template>
  </v-select>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getModels } from '../api/index'

const props = defineProps({ modelValue: { type: String, default: '' } })
const emit  = defineEmits(['update:modelValue'])

const rawModels = ref([])
const loading   = ref(false)
const error     = ref('')
const selected  = ref(props.modelValue)

const models = computed(() =>
  rawModels.value.map((m) => ({
    name:    m.name,
    display: `${m.name} (${m.model_id})`,
  }))
)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await getModels()
    rawModels.value = data
    if (data.length && !selected.value) {
      selected.value = data[0].name
      emit('update:modelValue', selected.value)
    }
  } catch (e) {
    error.value = '模型列表加载失败'
  } finally {
    loading.value = false
  }
})
</script>
