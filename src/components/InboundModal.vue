<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">📥 物资入库</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>

        <div class="form-group">
          <label class="form-label">入库仓库</label>
          <div class="wh-display">
            <span class="wh-chip" :class="targetWarehouse?.name === '回收仓' ? 'recycling' : 'main'">
              {{ targetWarehouse?.name || '选择仓库' }}
            </span>
            <span v-if="targetWarehouse?.location_desc" class="wh-desc">{{ targetWarehouse.location_desc }}</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">选择储位 <span class="optional">(可选)</span></label>
          <select class="form-select" v-model="selectedLocationId">
            <option :value="null">不指定储位</option>
            <option v-for="loc in locations" :key="loc.id" :value="loc.id">
              {{ loc.full_code }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">选择物资 <span class="required">*</span></label>
          <select class="form-select" v-model="selectedMaterialId" @change="onMaterialChange">
            <option :value="null">请选择物资</option>
            <option v-for="m in availableMaterials" :key="m.id" :value="m.id">
              {{ m.icon }} {{ m.name }}
              <template v-if="m.has_individual_tracking">(个体追踪 — 请用管理页添加)</template>
            </option>
          </select>
        </div>

        <div class="form-group" v-if="selectedMaterial && !selectedMaterial.has_individual_tracking">
          <label class="form-label">入库数量 <span class="required">*</span></label>
          <input
            class="form-input" type="number" v-model.number="quantity"
            min="1" placeholder="请输入入库数量" autocomplete="off"
          >
        </div>

        <div v-if="previewText" class="preview-box">
          <span class="preview-icon">📋</span>
          <span>{{ previewText }}</span>
        </div>

        <div v-if="showTrackingWarning" class="tracking-warning">
          ⚠️ 该物资为个体追踪类型，请使用物资管理页的"添加遥控器"功能入库。
        </div>

        <button class="btn-primary" @click="submit" :disabled="!canSubmit">
          确认入库
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { fetchWarehouses, fetchLocations } from '../api/warehouses.js'
import { fetchMaterials } from '../api/materials.js'
import { inbound } from '../api/inventory.js'

const props = defineProps({
  visible: Boolean,
  preselectedWarehouseId: Number,
})
const emit = defineEmits(['close', 'done'])

const warehouses = ref([])
const locations = ref([])
const allMaterials = ref([])
const selectedMaterialId = ref(null)
const selectedLocationId = ref(null)
const quantity = ref(1)
const submitting = ref(false)

const targetWarehouse = computed(() =>
  warehouses.value.find(w => w.id === props.preselectedWarehouseId)
)

const selectedMaterial = computed(() =>
  allMaterials.value.find(m => m.id === selectedMaterialId.value)
)

const showTrackingWarning = computed(() =>
  selectedMaterial.value?.has_individual_tracking
)

const availableMaterials = computed(() =>
  allMaterials.value.filter(m => m.category === 'consumable')
)

const previewText = computed(() => {
  if (!selectedMaterial.value || !targetWarehouse.value || quantity.value < 1) return ''
  const loc = locations.value.find(l => l.id === selectedLocationId.value)
  const locStr = loc ? ` → ${loc.full_code}` : ''
  return `将 ${quantity.value} ${selectedMaterial.value.unit} ${selectedMaterial.value.name} 入库到 ${targetWarehouse.value.name}${locStr}`
})

const canSubmit = computed(() =>
  selectedMaterialId.value && selectedMaterial.value &&
  !selectedMaterial.value.has_individual_tracking &&
  quantity.value > 0 &&
  !submitting.value
)

async function loadData() {
  const [whRes, matRes] = await Promise.all([
    fetchWarehouses(),
    fetchMaterials()
  ])
  if (whRes.ok) warehouses.value = whRes.data
  if (matRes.ok) allMaterials.value = matRes.data
}

async function loadLocations() {
  if (!props.preselectedWarehouseId) return
  const res = await fetchLocations(props.preselectedWarehouseId)
  if (res.ok) locations.value = res.data
}

function onMaterialChange() {
  // Reset warning state
}

watch(() => props.visible, (v) => {
  if (v) {
    loadData()
    loadLocations()
    selectedMaterialId.value = null
    selectedLocationId.value = null
    quantity.value = 1
  }
})

watch(() => props.preselectedWarehouseId, (v) => {
  if (v) loadLocations()
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  const res = await inbound({
    material_id: selectedMaterialId.value,
    warehouse_id: props.preselectedWarehouseId,
    location_id: selectedLocationId.value,
    quantity: quantity.value,
  })
  submitting.value = false
  if (res.ok) {
    emit('done', res)
  } else {
    alert(res.msg)
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(15,20,30,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.25s;
}
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-content {
  background: #fff; border-radius: 22px; padding: 28px 26px 22px;
  width: 92%; max-width: 460px; max-height: 85vh; overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18);
  transform: scale(0.92); transition: transform 0.25s;
}
.modal-overlay.active .modal-content { transform: scale(1); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.modal-title { font-size: 1.15rem; font-weight: 700; }
.required { color: #dc2626; }
.optional { font-size: 0.72rem; color: #8e9aab; font-weight: 400; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }

.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.84rem; font-weight: 600; color: #5a6b7d; margin-bottom: 6px; }
.form-input, .form-select {
  width: 100%; padding: 11px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.93rem;
  color: #1a2332; background: #f8fafc; transition: all 0.3s; outline: none;
  font-family: inherit; box-sizing: border-box;
}
.form-input:focus, .form-select:focus {
  border-color: #667eea; background: #fff;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

.wh-display {
  padding: 10px 14px; background: #f8fafc; border-radius: 10px;
  display: flex; align-items: center; gap: 10px;
}
.wh-chip {
  padding: 4px 12px; border-radius: 16px; font-size: 0.82rem; font-weight: 700;
}
.wh-chip.main { background: #ede9fe; color: #7c3aed; }
.wh-chip.recycling { background: #d1fae5; color: #065f46; }
.wh-desc { font-size: 0.78rem; color: #8e9aab; }

.preview-box {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 12px 16px; background: #f0f7ff; border-radius: 12px;
  margin-bottom: 16px; font-size: 0.86rem; color: #1a2332;
  border: 1px solid #dbeafe;
}
.preview-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }

.tracking-warning {
  padding: 12px 16px; background: #fef3c7; border-radius: 12px;
  margin-bottom: 16px; font-size: 0.84rem; color: #92400e;
  border: 1px solid #fde68a;
}

.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s; font-family: inherit;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }
</style>
