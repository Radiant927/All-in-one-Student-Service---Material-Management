<template>
  <Teleport to="body">
    <div class="management-overlay" :class="{ active: visible }" @click.self="$emit('close')"></div>
    <div class="management-page" :class="{ active: visible }">
      <div class="mgmt-topbar">
        <div class="mgmt-topbar-left">
          <span class="mgmt-title">{{ material?.icon }} {{ material?.name }} 管理</span>
          <div class="mgmt-stats">
            <span>总数: <span class="stat-total">{{ totalCount }}</span></span>
            <span>可借: <span class="stat-available">{{ availableCount }}</span></span>
            <span>已借出: <span class="stat-borrowed">{{ borrowedCount }}</span></span>
            <span>盘点缺失: <span class="stat-missing">{{ missingCount }}</span></span>
          </div>
        </div>
        <div class="mgmt-topbar-right">
          <button class="btn-sm" @click="$emit('print-all-qr')">🖨️ 打印全部二维码</button>
          <button class="btn-sm primary" @click="$emit('add-remote')">➕ 添加遥控器</button>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
      </div>
      <div class="mgmt-search">
        <input v-model="searchQuery" placeholder="🔍 搜索遥控器代号..." @input="onSearch">
      </div>
      <div class="mgmt-body">
        <div v-if="filteredItems.length === 0" class="mgmt-empty">
          <div class="mgmt-empty-icon">{{ searchQuery ? '🔍' : '📭' }}</div>
          <p>{{ searchQuery ? `没有匹配 "${searchQuery}" 的遥控器` : '暂无遥控器，点击"添加遥控器"开始' }}</p>
        </div>
        <div
          v-for="item in filteredItems"
          :key="item.code"
          class="remote-item-card"
          :class="item.status"
        >
          <div class="remote-code">🔑 {{ item.code }}</div>
          <span class="remote-status" :class="item.status">
            {{ statusLabel(item.status) }}
          </span>
          <div v-if="item.status === 'borrowed'" class="remote-borrower">
            借用人: <strong>{{ item.borrowedBy || '未知' }}</strong>
          </div>
          <div v-if="item.status === 'borrowed' && item.borrowTime" class="remote-time">
            借出: {{ formatTime(item.borrowTime) }}
          </div>
          <div class="remote-actions">
            <button class="btn-xs qr-item" @click="$emit('show-qr', item.code)">🔳 二维码</button>
            <button v-if="item.status === 'available'" class="btn-xs borrow-item" @click="$emit('borrow-item', item.code)">📤 借出</button>
            <button v-if="item.status === 'borrowed'" class="btn-xs return-item" @click="$emit('return-item', item.code)">📥 归还</button>
            <button v-if="item.status === 'available'" class="btn-xs danger" @click="$emit('delete-item', item.code)">🗑️</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from '../store/useStore.js'

const props = defineProps({
  visible: Boolean,
  material: Object
})

defineEmits(['close', 'show-qr', 'borrow-item', 'return-item', 'delete-item', 'add-remote', 'print-all-qr'])

const { loadItemsForMaterial } = useStore()

const searchQuery = ref('')

watch(() => props.visible, async (v) => {
  if (v && props.material?.has_individual_tracking) {
    await loadItemsForMaterial(props.material.id)
  }
})

const items = computed(() => props.material?.items || [])

const totalCount = computed(() => items.value.length)
const availableCount = computed(() => items.value.filter(i => i.status === 'available').length)
const borrowedCount = computed(() => items.value.filter(i => i.status === 'borrowed').length)
const missingCount = computed(() => items.value.filter(i => i.status === 'missing').length)

const filteredItems = computed(() => {
  if (!searchQuery.value.trim()) return items.value
  const q = searchQuery.value.trim().toLowerCase()
  return items.value.filter(i => i.code.toLowerCase().includes(q))
})

function onSearch() {}

function statusLabel(status) {
  return {
    available: '✅ 可用',
    borrowed: '📤 已借出',
    missing: '⚠️ 盘点缺失'
  }[status] || `⚠️ ${status}`
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
.management-overlay {
  position: fixed; inset: 0; z-index: 150;
  background: rgba(15,20,30,0.5); backdrop-filter: blur(4px);
  opacity: 0; pointer-events: none; transition: opacity 0.3s;
}
.management-overlay.active { opacity: 1; pointer-events: auto; }
.management-page {
  position: fixed; inset: 10px; z-index: 151;
  background: #f8fafc; border-radius: 22px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.2);
  transform: scale(0.94); opacity: 0; pointer-events: none;
  transition: all 0.3s;
  display: flex; flex-direction: column; overflow: hidden;
}
.management-page.active { transform: scale(1); opacity: 1; pointer-events: auto; }

.mgmt-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 22px; background: #fff;
  border-bottom: 1px solid #eef1f5; flex-shrink: 0;
  border-radius: 22px 22px 0 0;
}
.mgmt-topbar-left { display: flex; align-items: center; gap: 12px; }
.mgmt-title { font-size: 1.15rem; font-weight: 700; }
.mgmt-stats { display: flex; gap: 16px; margin-left: 12px; font-size: 0.8rem; color: #5a6b7d; }
.mgmt-stats span { white-space: nowrap; }
.stat-available { color: #059669; font-weight: 600; }
.stat-borrowed { color: #d97706; font-weight: 600; }
.stat-missing { color: #dc2626; font-weight: 600; }
.stat-total { color: #1a2332; font-weight: 600; }
.mgmt-topbar-right { display: flex; gap: 8px; align-items: center; }

.btn-sm {
  padding: 8px 16px; border-radius: 20px;
  border: 1.5px solid #dde4ed; background: #fff;
  cursor: pointer; font-size: 0.8rem; font-weight: 600;
  color: #5a6b7d; transition: all 0.3s; white-space: nowrap;
  display: flex; align-items: center; gap: 5px;
}
.btn-sm:hover { border-color: #667eea; color: #667eea; background: #f8faff; }
.btn-sm.primary { background: #667eea; color: #fff; border-color: #667eea; }
.btn-sm.primary:hover { background: #4c63d2; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s; margin-left: 4px;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }

.mgmt-search { padding: 12px 22px; background: #fff; flex-shrink: 0; border-bottom: 1px solid #f1f3f6; }
.mgmt-search input {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.88rem;
  outline: none; transition: all 0.3s; background: #f8fafc;
}
.mgmt-search input:focus { border-color: #667eea; background: #fff; box-shadow: 0 0 0 3px rgba(102,126,234,0.06); }

.mgmt-body {
  flex: 1; overflow-y: auto; padding: 16px 22px;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px; align-content: start;
}

.remote-item-card {
  background: #fff; border-radius: 12px; padding: 16px;
  border: 1.5px solid #eef1f5; text-align: center;
  transition: all 0.3s; position: relative;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.remote-item-card:hover { border-color: #ccd5e0; box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-2px); }
.remote-item-card.available { border-left: 4px solid #22c55e; }
.remote-item-card.borrowed { border-left: 4px solid #ef4444; background: #fefcfb; }
.remote-item-card.missing { border-left: 4px solid #f59e0b; background: #fffbeb; }
.remote-code { font-size: 1rem; font-weight: 800; color: #1a2332; }
.remote-status { font-size: 0.75rem; font-weight: 700; padding: 4px 12px; border-radius: 12px; display: inline-block; }
.remote-status.available { background: #d1fae5; color: #065f46; }
.remote-status.borrowed { background: #fee2e2; color: #991b1b; }
.remote-status.missing { background: #fef3c7; color: #92400e; }
.remote-borrower { font-size: 0.78rem; color: #5a6b7d; }
.remote-borrower strong { color: #1a2332; }
.remote-time { font-size: 0.7rem; color: #8e9aab; }
.remote-actions { display: flex; gap: 8px; margin-top: 4px; }
.btn-xs {
  padding: 6px 12px; border-radius: 15px;
  border: 1.5px solid #dde4ed; background: #fff;
  cursor: pointer; font-size: 0.72rem; font-weight: 600; transition: all 0.3s;
}
.btn-xs:hover { transform: translateY(-1px); }
.btn-xs.borrow-item { background: #667eea; color: #fff; border-color: #667eea; }
.btn-xs.borrow-item:hover { background: #4c63d2; }
.btn-xs.return-item { color: #2cc45e; border-color: #43e97b; }
.btn-xs.return-item:hover { background: rgba(67,233,123,0.08); }
.btn-xs.qr-item { color: #5a6b7d; }
.btn-xs.qr-item:hover { border-color: #888; color: #333; }
.btn-xs.danger { color: #dc2626; border-color: #fecaca; }
.btn-xs.danger:hover { border-color: #dc2626; background: #fef2f2; }

.mgmt-empty { grid-column: 1 / -1; text-align: center; padding: 48px 20px; color: #8e9aab; }
.mgmt-empty-icon { font-size: 48px; margin-bottom: 12px; }

@media (max-width: 768px) {
  .management-page { inset: 4px; border-radius: 12px; }
  .mgmt-topbar { padding: 12px 14px; flex-wrap: wrap; gap: 8px; }
  .mgmt-stats { margin-left: 0; gap: 10px; }
  .mgmt-body { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; padding: 12px; }
  .mgmt-search { padding: 10px 14px; }
  .remote-item-card { padding: 12px; }
  .btn-sm { font-size: 0.72rem; padding: 6px 10px; }
}
</style>
