<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">➕ 添加遥控器</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="form-group">
          <label class="form-label">起始代号</label>
          <input class="form-input" v-model="prefix" placeholder="例如: AC">
        </div>
        <div class="add-remote-row">
          <div class="form-group">
            <label class="form-label">起始编号</label>
            <input class="form-input" v-model.number="startNum" type="number" min="1">
          </div>
          <div class="form-group">
            <label class="form-label">添加数量</label>
            <input class="form-input" v-model.number="count" type="number" min="1" max="50">
          </div>
        </div>
        <p class="hint">示例: 从 AC-21 开始添加 5 个 → 生成 AC-021 ~ AC-025</p>
        <button class="btn-primary" @click="$emit('confirm', { prefix, startNum, count })">确认添加</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  nextStartNum: Number
})

defineEmits(['close', 'confirm'])

const prefix = ref('AC')
const startNum = ref(1)
const count = ref(1)

watch(() => props.visible, (v) => {
  if (v) {
    prefix.value = 'AC'
    startNum.value = props.nextStartNum || 1
    count.value = 1
  }
})
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
  width: 92%; max-width: 440px;
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
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.84rem; font-weight: 600; color: #5a6b7d; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 11px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.93rem;
  color: #1a2332; background: #f8fafc; transition: all 0.3s; outline: none;
}
.form-input:focus { border-color: #667eea; background: #fff; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
.add-remote-row { display: flex; gap: 10px; align-items: flex-end; }
.add-remote-row .form-group { flex: 1; margin-bottom: 0; }
.hint { font-size: 0.72rem; color: #8e9aab; margin: 6px 0 12px; }
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
</style>
