<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">📥 导入物资数据</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div
          class="drop-zone"
          :class="{ dragging }"
          @dragover.prevent="dragging = true"
          @dragleave="dragging = false"
          @drop.prevent="onDrop"
          @click="fileInput?.click()"
        >
          <div class="drop-icon">📁</div>
          <p v-if="!selectedFile">拖拽 Excel 文件到此处，或点击选择</p>
          <p v-else class="selected-file">已选择: {{ selectedFile.name }}</p>
          <input type="file" ref="fileInput" accept=".xlsx,.xls" @change="onFileChange" hidden>
        </div>
        <button class="btn-primary" @click="upload" :disabled="!selectedFile || uploading">
          {{ uploading ? '导入中...' : '开始导入' }}
        </button>
        <div v-if="result" class="import-result">
          <p>✅ 导入成功: <strong>{{ result.imported }}</strong> 条</p>
          <p v-if="result.skipped">⏭️ 跳过: <strong>{{ result.skipped }}</strong> 条</p>
          <div v-if="result.errors?.length" class="import-errors">
            <p class="error-title">⚠️ 错误:</p>
            <ul>
              <li v-for="(e, i) in result.errors" :key="i">{{ e }}</li>
            </ul>
          </div>
        </div>
        <p class="hint">Excel 表头: 品名, 规格, 单位, 数量, 分类, 子分类, 仓库, 储位, 个体追踪, 预警阈值</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { importExcel } from '../api/import.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'imported'])

const fileInput = ref(null)
const selectedFile = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const result = ref(null)

function onFileChange(e) {
  selectedFile.value = e.target.files[0]
  result.value = null
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
    selectedFile.value = file
    result.value = null
  }
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  const res = await importExcel(selectedFile.value)
  if (res.ok) {
    result.value = res.data
    emit('imported')
  } else {
    result.value = { imported: 0, skipped: 0, errors: [res.msg] }
  }
  uploading.value = false
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(15,20,30,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.25s;
}
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-content {
  background: #fff; border-radius: 22px; padding: 28px 26px 22px;
  width: 92%; max-width: 460px; max-height: 80vh; overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18);
  transform: scale(0.92); transition: transform 0.25s;
}
.modal-overlay.active .modal-content { transform: scale(1); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.modal-title { font-size: 1.15rem; font-weight: 700; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }
.drop-zone {
  border: 2px dashed #dde4ed; border-radius: 16px;
  padding: 36px 20px; text-align: center; cursor: pointer;
  margin-bottom: 16px; transition: all 0.3s;
  color: #8e9aab; font-size: 0.88rem;
}
.drop-zone:hover, .drop-zone.dragging { border-color: #667eea; background: rgba(102,126,234,0.04); }
.drop-zone.dragging { border-color: #4facfe; background: rgba(79,172,254,0.06); }
.drop-icon { font-size: 40px; margin-bottom: 8px; }
.selected-file { color: #667eea; font-weight: 600; }
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }
.import-result { margin-top: 16px; padding: 14px; background: #f8fafc; border-radius: 12px; }
.import-result p { font-size: 0.86rem; margin-bottom: 4px; }
.import-errors { margin-top: 8px; }
.error-title { color: #dc2626; font-weight: 600; }
.import-errors ul { margin: 4px 0 0 16px; font-size: 0.78rem; color: #dc2626; }
.hint { font-size: 0.72rem; color: #8e9aab; margin-top: 12px; text-align: center; }
</style>