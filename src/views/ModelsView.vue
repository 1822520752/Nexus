<script setup lang="ts">
/**
 * 模型管理视图组件
 * 提供模型配置和管理界面
 */
import { ref, computed } from 'vue'
import { useModelsStore } from '@/stores/models'
import type { AIModel } from '@/types'

const modelsStore = useModelsStore()

/**
 * 模型列表
 */
const models = computed(() => modelsStore.models)

/**
 * 是否显示添加模型对话框
 */
const showAddDialog = ref(false)

/**
 * 新模型表单
 */
const newModel = ref<Partial<AIModel>>({
  name: '',
  provider: 'local',
  endpoint: '',
  maxTokens: 4096,
  temperature: 0.7,
  contextWindow: 8192,
  enabled: true
})

/**
 * 提供商选项
 */
const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'local', label: '本地模型' },
  { value: 'custom', label: '自定义' }
]

/**
 * 添加新模型
 */
const addModel = async () => {
  if (!newModel.value.name) return

  await modelsStore.addModel(newModel.value as Omit<AIModel, 'id' | 'createdAt' | 'updatedAt'>)
  showAddDialog.value = false
  resetForm()
}

/**
 * 删除模型
 * @param modelId - 模型 ID
 */
const deleteModel = async (modelId: string) => {
  if (confirm('确定要删除此模型吗？')) {
    await modelsStore.deleteModel(modelId)
  }
}

/**
 * 切换模型启用状态
 * @param modelId - 模型 ID
 */
const toggleModel = async (modelId: string) => {
  await modelsStore.toggleModel(modelId)
}

/**
 * 重置表单
 */
const resetForm = () => {
  newModel.value = {
    name: '',
    provider: 'local',
    endpoint: '',
    maxTokens: 4096,
    temperature: 0.7,
    contextWindow: 8192,
    enabled: true
  }
}
</script>

<template>
  <div class="min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
      <!-- 头部 -->
      <header class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-white mb-2">模型管理</h1>
          <p class="text-secondary-400">配置和管理 AI 模型</p>
        </div>
        <button
          class="btn-primary"
          @click="showAddDialog = true"
        >
          添加模型
        </button>
      </header>

      <!-- 模型列表 -->
      <div class="space-y-4">
        <div
          v-for="model in models"
          :key="model.id"
          class="card flex items-center justify-between"
        >
          <div class="flex items-center gap-4">
            <!-- 模型图标 -->
            <div class="w-12 h-12 rounded-lg bg-primary-500/20 flex items-center justify-center">
              <span class="text-2xl">🤖</span>
            </div>

            <!-- 模型信息 -->
            <div>
              <h3 class="text-lg font-semibold text-white">{{ model.name }}</h3>
              <p class="text-sm text-secondary-400">
                {{ providerOptions.find(p => p.value === model.provider)?.label }}
                <span class="mx-2">|</span>
                {{ model.maxTokens }} tokens
                <span class="mx-2">|</span>
                温度: {{ model.temperature }}
              </p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-3">
            <button
              :class="[
                'relative w-12 h-6 rounded-full transition-colors',
                model.enabled ? 'bg-primary-600' : 'bg-secondary-700'
              ]"
              @click="toggleModel(model.id)"
            >
              <span
                :class="[
                  'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                  model.enabled ? 'left-7' : 'left-1'
                ]"
              ></span>
            </button>
            <button
              class="btn-ghost text-red-400 hover:text-red-300"
              @click="deleteModel(model.id)"
            >
              删除
            </button>
          </div>
        </div>

        <!-- 空状态 -->
        <div
          v-if="models.length === 0"
          class="card text-center py-12"
        >
          <p class="text-secondary-400 mb-4">暂无模型配置</p>
          <button
            class="btn-primary"
            @click="showAddDialog = true"
          >
            添加第一个模型
          </button>
        </div>
      </div>

      <!-- 添加模型对话框 -->
      <div
        v-if="showAddDialog"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showAddDialog = false"
      >
        <div class="card w-full max-w-md">
          <h2 class="text-xl font-semibold text-white mb-6">添加新模型</h2>

          <form @submit.prevent="addModel" class="space-y-4">
            <!-- 模型名称 -->
            <div>
              <label class="block text-white mb-2">模型名称</label>
              <input
                v-model="newModel.name"
                type="text"
                class="input"
                placeholder="例如: GPT-4"
                required
              />
            </div>

            <!-- 提供商 -->
            <div>
              <label class="block text-white mb-2">提供商</label>
              <select
                v-model="newModel.provider"
                class="input"
              >
                <option
                  v-for="option in providerOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>

            <!-- 端点地址 -->
            <div>
              <label class="block text-white mb-2">端点地址</label>
              <input
                v-model="newModel.endpoint"
                type="text"
                class="input"
                placeholder="http://localhost:11434"
              />
            </div>

            <!-- 最大 Tokens -->
            <div>
              <label class="block text-white mb-2">最大 Tokens</label>
              <input
                v-model.number="newModel.maxTokens"
                type="number"
                class="input"
                min="1"
              />
            </div>

            <!-- 温度 -->
            <div>
              <label class="block text-white mb-2">温度 (0-2)</label>
              <input
                v-model.number="newModel.temperature"
                type="number"
                class="input"
                min="0"
                max="2"
                step="0.1"
              />
            </div>

            <!-- 按钮 -->
            <div class="flex gap-3 pt-4">
              <button
                type="button"
                class="btn-secondary flex-1"
                @click="showAddDialog = false"
              >
                取消
              </button>
              <button
                type="submit"
                class="btn-primary flex-1"
              >
                添加
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
