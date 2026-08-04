// 全局 toast 系统 — 任何组件 import { toast } from '../utils/toast.js' 即可使用
import { ref } from 'vue'

const toasts = ref([])
let _id = 0

const iconMap = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' }

export function toast(message, type = 'info') {
  const id = ++_id
  toasts.value.push({ id, message, type, icon: iconMap[type] || iconMap.info })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 2600)
}

// 供 ToastContainer 组件读取的响应式列表
export function useToastState() {
  return { toasts, iconMap }
}
