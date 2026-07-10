<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">📥 归还遥控器 {{ itemCode }}</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="form-group">
          <label class="form-label">遥控器代号</label>
          <input class="form-input" :value="itemCode" readonly style="background:#f1f5f9;font-weight:700;">
        </div>
        <div class="form-group">
          <label class="form-label">当前借用人: <strong style="color:#d97706;">{{ currentBorrower }}</strong></label>
        </div>
        <div class="form-group">
          <label class="form-label">归还人姓名</label>
          <input class="form-input" v-model="returner" placeholder="请输入归还人姓名" @keydown.enter="confirm" ref="inputRef">
        </div>
        <button class="btn-primary" @click="confirm">确认归还</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  itemCode: String,
  currentBorrower: String
})

const emit = defineEmits(['close', 'confirm'])

const returner = ref('')
const inputRef = ref(null)

watch(() => props.visible, (v) => {
  if (v) {
    returner.value = ''
    setTimeout(() => inputRef.value?.focus(), 200)
  }
})

function confirm() {
  emit('confirm', { itemCode: props.itemCode, returner: returner.value })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 160;
  background: rgba(15,20,30,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.25s;
}
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-content {
  background: #fff; border-radius: 22px; padding: 28px 26px 22px;
  width: 92%; max-width: 420px;
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
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
</style>
