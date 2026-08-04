<template>
  <div class="warehouse-page">
    <div class="view-toggle-bar">
      <button class="view-toggle-btn" :class="{ active: !showWarehouse }" @click="$emit('view-all')">
        📋 全部物资
      </button>
      <button class="view-toggle-btn active">
        🏗️ 仓库视图
      </button>
    </div>

    <div class="warehouse-card-grid">
      <div
        v-for="wh in stats"
        :key="wh.id"
        class="warehouse-card"
        :class="wh.name === '回收仓' ? 'card-recycling' : 'card-main'"
        @click="$emit('view-detail', wh.id)"
      >
        <div class="warehouse-card-header">
          <div class="warehouse-card-icon" :class="wh.name === '回收仓' ? 'recycling' : 'main'">
            {{ wh.name === '回收仓' ? '♻️' : '🏭' }}
          </div>
          <div>
            <div class="warehouse-card-name">{{ wh.name }}</div>
            <div class="warehouse-card-desc">{{ wh.location_desc || '仓库' }}</div>
          </div>
        </div>
        <div class="warehouse-card-stats">
          <div class="wh-stat-item">
            <div class="wh-stat-value types">{{ wh.materials_count }}</div>
            <div class="wh-stat-label">物资种类</div>
          </div>
          <div class="wh-stat-item">
            <div class="wh-stat-value total">{{ wh.total_quantity }}</div>
            <div class="wh-stat-label">总数量</div>
          </div>
          <div class="wh-stat-item">
            <div class="wh-stat-value" :class="wh.low_stock_count > 0 ? 'warning' : 'available'">
              {{ wh.low_stock_count }}
            </div>
            <div class="wh-stat-label">低库存预警</div>
          </div>
        </div>
        <div class="warehouse-card-footer">
          <span class="view-detail-link">查看详情 →</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { fetchWarehouseStats } from '../api/warehouses.js'

defineProps({
  showWarehouse: { type: Boolean, default: true }
})

defineEmits(['view-detail', 'view-all'])

const stats = ref([])

async function loadStats() {
  const res = await fetchWarehouseStats()
  if (res.ok) stats.value = res.data
}

onMounted(loadStats)
</script>

<style scoped>
.warehouse-page { margin-bottom: 24px; }

.view-toggle-bar {
  display: flex; gap: 10px; margin-bottom: 20px;
}
.view-toggle-btn {
  padding: 10px 20px; border-radius: 12px; border: 1.5px solid #dde4ed;
  background: rgba(255,255,255,0.7); cursor: pointer; font-size: 0.88rem;
  font-weight: 600; color: #5a6b7d; transition: all 0.3s;
  backdrop-filter: blur(14px); font-family: inherit;
}
.view-toggle-btn:hover { border-color: #667eea; color: #667eea; }
.view-toggle-btn.active {
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; border-color: transparent;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
}

.warehouse-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}
.warehouse-card {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px; padding: 24px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  cursor: pointer; transition: all 0.3s;
  position: relative; overflow: hidden;
}
.warehouse-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  transition: height 0.3s;
}
.warehouse-card.card-main::before {
  background: linear-gradient(90deg, #667eea, #4facfe);
}
.warehouse-card.card-recycling::before {
  background: linear-gradient(90deg, #43e97b, #38f9d7);
}
.warehouse-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(0,0,0,0.13);
}
.warehouse-card:hover::before { height: 6px; }

.warehouse-card-header {
  display: flex; align-items: center; gap: 14px; margin-bottom: 18px;
}
.warehouse-card-icon {
  width: 52px; height: 52px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center; font-size: 26px;
  flex-shrink: 0;
}
.warehouse-card-icon.main {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe); color: #667eea;
}
.warehouse-card-icon.recycling {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0); color: #059669;
}
.warehouse-card-name { font-size: 1.1rem; font-weight: 700; color: #1a2332; }
.warehouse-card-desc { font-size: 0.78rem; color: #8e9aab; margin-top: 2px; }

.warehouse-card-stats {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  margin-bottom: 14px;
}
.wh-stat-item {
  text-align: center; padding: 10px 6px;
  background: rgba(0,0,0,0.02); border-radius: 12px;
}
.wh-stat-value { font-size: 1.4rem; font-weight: 800; }
.wh-stat-value.types { color: #667eea; }
.wh-stat-value.total { color: #1a2332; }
.wh-stat-value.available { color: #059669; }
.wh-stat-value.warning { color: #dc2626; }
.wh-stat-label { font-size: 0.72rem; color: #8e9aab; margin-top: 2px; }

.warehouse-card-footer { text-align: right; }
.view-detail-link { font-size: 0.82rem; color: #667eea; font-weight: 600; }

@media (max-width: 768px) {
  .warehouse-card-grid { grid-template-columns: 1fr; }
}
</style>
