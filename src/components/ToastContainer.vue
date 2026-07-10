<template>
  <Teleport to="body">
    <div class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <span>{{ iconMap[toast.type] }}</span> {{ toast.message }}
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0
const iconMap = { success: '✅', error: '❌', info: 'ℹ️' }

function show(message, type = 'info') {
  const id = ++idCounter
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 2600)
}

defineExpose({ show })
</script>

<style scoped>
.toast-container {
  position: fixed; top: 20px; right: 20px; z-index: 500;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}
.toast {
  padding: 13px 18px; border-radius: 12px; color: #fff;
  font-size: 0.86rem; font-weight: 600; max-width: 360px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.16);
  animation: toastIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto; display: flex; align-items: center; gap: 9px;
}
.toast.success { background: linear-gradient(135deg, #22c55e, #16a34a); }
.toast.error { background: linear-gradient(135deg, #ef4444, #dc2626); }
.toast.info { background: linear-gradient(135deg, #3b82f6, #2563eb); }
@keyframes toastIn {
  from { opacity: 0; transform: translateY(-20px) scale(0.94); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@media (max-width: 768px) {
  .toast-container { left: 12px; right: 12px; }
  .toast { max-width: 100%; }
}
</style>
