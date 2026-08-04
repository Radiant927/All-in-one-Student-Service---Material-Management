<template>
  <section class="history-section">
    <div class="history-header" @click="open = !open">
      <div class="history-title">
        <span class="history-title-icon">📋</span> 借用记录
      </div>
      <span class="history-chevron" :class="{ open }">▼</span>
    </div>
    <div class="history-body" :class="{ open }">
      <ul class="history-list">
        <li v-if="history.length === 0" class="history-empty">暂无借用记录</li>
        <li v-for="h in history" :key="h.id" class="history-item">
          <span class="history-dot" :class="h.action"></span>
          <span class="history-info">
            <template v-if="h.action === 'borrow'">
              {{ h.borrower || '未知' }} 借出
              <span v-if="h.item_code" class="item-code">[{{ h.item_code }}]</span>
              <strong>{{ h.quantity }}</strong> 个{{ h.material_name || getMaterialName(h.material_id) }}
            </template>
            <template v-else>
              归还
              <span v-if="h.item_code" class="item-code">[{{ h.item_code }}]</span>
              <strong>{{ h.quantity }}</strong> 个{{ h.material_name || getMaterialName(h.material_id) }}
              <span v-if="h.returned_by"> (归还人: {{ h.returned_by }})</span>
            </template>
          </span>
          <span class="history-time">{{ formatTime(h.created_at) }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  history: Array,
  materials: Array
})

const open = ref(false)

function getMaterialName(id) {
  if (props.materials) {
    const m = props.materials.find(x => x.id === id)
    if (m) return (m.icon || '') + m.name
  }
  return '未知物资'
}

function formatTime(iso) {
  const d = new Date(iso)
  const now = new Date()
  const diffMin = Math.floor((now - d) / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 7) return `${diffDay} 天前`
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day}`
}
</script>

<style scoped>
.history-section { margin-bottom: 28px; }
.history-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 15px 22px; cursor: pointer;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  transition: all 0.3s;
}
.history-header:hover { box-shadow: 0 16px 48px rgba(0,0,0,0.13); }
.history-title { display: flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; color: #1a2332; }
.history-chevron { font-size: 14px; color: #8e9aab; transition: transform 0.3s; }
.history-chevron.open { transform: rotate(180deg); }
.history-body { max-height: 0; overflow: hidden; transition: max-height 0.45s cubic-bezier(0.4, 0, 0.2, 1); }
.history-body.open { max-height: 500px; overflow-y: auto; }
.history-list { list-style: none; padding: 6px 0 0; }
.history-item { display: flex; align-items: center; gap: 12px; padding: 11px 18px; margin: 0 4px; border-radius: 10px; font-size: 0.86rem; transition: background 0.3s; }
.history-item:hover { background: rgba(0,0,0,0.02); }
.history-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.history-dot.borrow { background: #f59e0b; }
.history-dot.return { background: #22c55e; }
.history-info { flex: 1; color: #1a2332; }
.item-code { font-size: 0.75rem; color: #667eea; font-weight: 600; }
.history-time { font-size: 0.75rem; color: #8e9aab; white-space: nowrap; }
.history-empty { text-align: center; padding: 28px; color: #8e9aab; font-size: 0.88rem; }
</style>
