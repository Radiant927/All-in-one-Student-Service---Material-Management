<template>
  <div class="wh-detail">
    <div class="wh-detail-back" @click="$emit('back')">← 返回仓库总览</div>

    <div class="wh-detail-header">
      <div class="wh-detail-icon" :class="detail.name === '回收仓' ? 'recycling' : 'main'">
        {{ detail.name === '回收仓' ? '♻️' : '🏭' }}
      </div>
      <div class="wh-detail-info">
        <div class="wh-detail-name">{{ detail.name }}</div>
        <div class="wh-detail-meta">
          <span>{{ detail.location_desc || '仓库' }}</span>
          <span>·</span>
          <span>{{ materials.length }} 种物资</span>
          <span>·</span>
          <span>{{ locations.length }} 个储位</span>
        </div>
      </div>
      <div class="wh-detail-actions">
        <button class="btn-action btn-inbound" @click="$emit('inbound', warehouseId)">📥 入库</button>
        <button class="btn-action btn-transfer" @click="$emit('transfer', warehouseId)">🔄 调拨</button>
      </div>
    </div>

    <div class="wh-detail-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'materials' }" @click="activeTab = 'materials'">
        📦 物资列表
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'locations' }" @click="activeTab = 'locations'">
        📍 储位管理
      </button>
    </div>

    <!-- Materials Tab -->
    <div v-if="activeTab === 'materials'" class="card-grid">
      <div v-if="materials.length === 0" class="empty-state">该仓库暂无物资</div>
      <div
        v-for="m in materials"
        :key="m.id"
        class="wh-material-card"
      >
        <div class="wh-material-top">
          <span class="wh-material-icon">{{ m.icon }}</span>
          <span class="wh-material-name">{{ m.name }}</span>
          <span class="sub-tag" :class="'tag-' + m.sub_category">{{ subCatLabel(m.sub_category) }}</span>
        </div>
        <div class="wh-material-body">
          <div class="wh-mat-stat">
            <span class="wh-mat-val">{{ m.total_quantity }}</span>
            <span class="wh-mat-lbl">{{ m.unit }}</span>
          </div>
          <div v-if="m.location_code" class="wh-mat-loc">📍 {{ m.location_code }}</div>
        </div>
        <div v-if="m.low_stock_threshold > 0 && m.total_quantity <= m.low_stock_threshold" class="low-stock-alert">
          ⚠️ 库存不足（阈值: {{ m.low_stock_threshold }}）
        </div>
      </div>
    </div>

    <!-- Locations Tab -->
    <div v-if="activeTab === 'locations'" class="locations-panel">
      <div class="loc-add-row">
        <select class="form-select loc-wh-select" disabled>
          <option>{{ detail.name }}</option>
        </select>
        <input class="form-input loc-shelf" v-model="newLoc.shelf" placeholder="货架 (如 A)" maxlength="5">
        <input class="form-input loc-level" v-model.number="newLoc.level" type="number" placeholder="层" min="1">
        <input class="form-input loc-pos" v-model="newLoc.position" placeholder="位 (如 2)" maxlength="5">
        <button class="btn-add-loc" @click="addLocation" :disabled="!canAddLoc">添加</button>
      </div>
      <div v-if="locations.length === 0" class="empty-state">暂无储位</div>
      <div v-for="loc in locations" :key="loc.id" class="loc-item">
        <span class="loc-code">📍 {{ loc.full_code }}</span>
        <button class="btn-loc-del" @click="deleteLocation(loc.id)" title="删除">🗑️</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, reactive, computed } from 'vue'
import { toast } from '../utils/toast.js'
import { fetchWarehouseDetail, createLocation, deleteLocation as apiDeleteLocation } from '../api/warehouses.js'

const props = defineProps({
  warehouseId: Number,
})
const emit = defineEmits(['back', 'inbound', 'transfer'])

const detail = ref({ name: '', location_desc: '' })
const materials = ref([])
const locations = ref([])
const activeTab = ref('materials')

const newLoc = reactive({ shelf: '', level: 1, position: '' })
const canAddLoc = computed(() => newLoc.shelf.trim() && newLoc.level > 0)

function subCatLabel(sub) {
  const map = {
    new_consumable: '新品消耗', recyclable: '可回收', direct_consumption: '直接消耗'
  }
  return map[sub] || sub || ''
}

async function loadData() {
  if (!props.warehouseId) return
  const res = await fetchWarehouseDetail(props.warehouseId)
  if (res.ok) {
    detail.value = res.data
    materials.value = res.data.materials || []
    locations.value = res.data.locations || []
  }
}

async function addLocation() {
  const res = await createLocation({
    warehouse_id: props.warehouseId,
    shelf: newLoc.shelf.trim(),
    level: newLoc.level,
    position: newLoc.position.trim(),
  })
  if (res.ok) {
    newLoc.shelf = ''
    newLoc.level = 1
    newLoc.position = ''
    await loadData()
  } else {
    toast(res.msg, 'error')
  }
}

async function deleteLocation(id) {
  if (!confirm('确定删除此储位吗？')) return
  const res = await apiDeleteLocation(id)
  if (res.ok) {
    await loadData()
  } else {
    toast(res.msg, 'error')
  }
}

onMounted(loadData)
watch(() => props.warehouseId, (v) => { if (v) loadData() })
</script>

<style scoped>
.wh-detail { margin-bottom: 24px; }
.wh-detail-back {
  display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
  color: #667eea; font-weight: 600; font-size: 0.9rem;
  margin-bottom: 16px; transition: opacity 0.3s;
}
.wh-detail-back:hover { opacity: 0.7; }

.wh-detail-header {
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
  padding: 20px 24px; background: rgba(255,255,255,0.82);
  backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px; box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}
.wh-detail-icon {
  width: 56px; height: 56px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; flex-shrink: 0;
}
.wh-detail-icon.main { background: linear-gradient(135deg, #e0e7ff, #c7d2fe); color: #667eea; }
.wh-detail-icon.recycling { background: linear-gradient(135deg, #d1fae5, #a7f3d0); color: #059669; }
.wh-detail-info { flex: 1; }
.wh-detail-name { font-size: 1.25rem; font-weight: 700; color: #1a2332; }
.wh-detail-meta { font-size: 0.8rem; color: #8e9aab; margin-top: 4px; display: flex; gap: 6px; }
.wh-detail-actions { display: flex; gap: 8px; }
.btn-action {
  padding: 9px 18px; border-radius: 12px; border: none;
  font-size: 0.84rem; font-weight: 600; cursor: pointer; transition: all 0.3s;
  font-family: inherit;
}
.btn-inbound {
  background: linear-gradient(135deg, #667eea, #4facfe); color: #fff;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
}
.btn-inbound:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-transfer {
  background: transparent; color: #059669;
  border: 2px solid #43e97b;
}
.btn-transfer:hover { background: rgba(67,233,123,0.08); transform: translateY(-1px); }

.wh-detail-tabs { display: flex; gap: 8px; margin-bottom: 18px; }
.tab-btn {
  padding: 8px 18px; border-radius: 10px; border: 1.5px solid #dde4ed;
  background: rgba(255,255,255,0.7); cursor: pointer; font-size: 0.84rem;
  font-weight: 600; color: #5a6b7d; transition: all 0.3s; font-family: inherit;
}
.tab-btn:hover { border-color: #667eea; color: #667eea; }
.tab-btn.active {
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; border-color: transparent;
  box-shadow: 0 4px 12px rgba(102,126,234,0.25);
}

.card-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;
}
.wh-material-card {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 18px; padding: 18px 20px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.05);
  transition: all 0.3s;
}
.wh-material-card:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.1); }
.wh-material-top { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.wh-material-icon { font-size: 24px; }
.wh-material-name { font-weight: 700; color: #1a2332; font-size: 0.95rem; flex: 1; }
.sub-tag {
  font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 8px;
}
.tag-new_consumable { background: #dbeafe; color: #2563eb; }
.tag-recyclable { background: #fef3c7; color: #d97706; }
.tag-direct_consumption { background: #fee2e2; color: #dc2626; }

.wh-material-body { display: flex; align-items: center; justify-content: space-between; }
.wh-mat-stat { display: flex; align-items: baseline; gap: 4px; }
.wh-mat-val { font-size: 1.5rem; font-weight: 800; color: #667eea; }
.wh-mat-lbl { font-size: 0.78rem; color: #8e9aab; }
.wh-mat-loc { font-size: 0.78rem; color: #8e9aab; background: #f8fafc; padding: 3px 10px; border-radius: 8px; }

.low-stock-alert {
  margin-top: 10px; padding: 6px 12px; background: #fef2f2; color: #dc2626;
  border-radius: 10px; font-size: 0.76rem; font-weight: 600;
  border: 1px solid #fecaca;
}

.locations-panel { max-width: 600px; }
.loc-add-row { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
.form-select, .form-input {
  padding: 10px 12px; border-radius: 10px; font-size: 0.88rem;
  border: 1.5px solid #dde4ed; background: #f8fafc;
  color: #1a2332; outline: none; transition: all 0.3s; font-family: inherit;
}
.form-select:focus, .form-input:focus {
  border-color: #667eea; background: #fff;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}
.form-select:disabled { opacity: 0.7; }
.loc-wh-select { width: 120px; }
.loc-shelf { width: 80px; }
.loc-level { width: 70px; }
.loc-pos { width: 70px; }
.btn-add-loc {
  padding: 10px 16px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.84rem; font-weight: 600; cursor: pointer;
  transition: all 0.3s; font-family: inherit; white-space: nowrap;
}
.btn-add-loc:hover { box-shadow: 0 4px 14px rgba(102,126,234,0.3); }
.btn-add-loc:disabled { background: #ccd0d8; cursor: not-allowed; box-shadow: none; }

.loc-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 12px;
  background: #f8fafc; margin-bottom: 8px; border: 1px solid #eef1f5;
}
.loc-code { font-weight: 700; color: #1a2332; flex: 1; font-size: 0.9rem; }
.btn-loc-del {
  background: none; border: none; cursor: pointer; font-size: 16px;
  padding: 4px 8px; border-radius: 6px; transition: all 0.2s;
}
.btn-loc-del:hover { background: #fef2f2; }

.empty-state { text-align: center; color: #8e9aab; padding: 40px; font-size: 0.9rem; grid-column: 1/-1; }

@media (max-width: 768px) {
  .wh-detail-header { flex-wrap: wrap; gap: 12px; }
  .wh-detail-actions { width: 100%; }
  .wh-detail-actions .btn-action { flex: 1; text-align: center; }
  .loc-add-row { flex-wrap: wrap; }
}
</style>
