<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">🔄 仓库调拨</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>

        <div class="form-group">
          <label class="form-label">调出仓库</label>
          <select class="form-select" v-model="fromWarehouseId" @change="onFromChange">
            <option :value="null">选择调出仓库</option>
            <option v-for="wh in warehouses" :key="wh.id" :value="wh.id">
              {{ wh.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">调入仓库</label>
          <select class="form-select" v-model="toWarehouseId">
            <option :value="null">选择调入仓库</option>
            <option v-for="wh in toWarehouseOptions" :key="wh.id" :value="wh.id">
              {{ wh.name }}
            </option>
          </select>
        </div>

        <div class="form-group" v-if="fromMaterials.length > 0">
          <label class="form-label">选择物资 <span class="required">*</span></label>
          <select class="form-select" v-model="selectedMaterialId" @change="onMaterialChange">
            <option :value="null">请选择物资</option>
            <option v-for="m in fromMaterials" :key="m.id" :value="m.id">
              {{ m.icon }} {{ m.name }} ({{ m.total_quantity }} {{ m.unit }})
            </option>
          </select>
        </div>
        <div v-else-if="fromWarehouseId" class="empty-hint">该仓库暂无物资可调拨</div>

        <div class="form-group" v-if="selectedMaterial && !selectedMaterial.has_individual_tracking">
          <label class="form-label">调拨数量 <span class="required">*</span></label>
          <div class="qty-row">
            <input
              class="form-input qty-input" type="number" v-model.number="quantity"
              :max="maxQuantity" min="1" autocomplete="off"
            >
            <span class="qty-hint">可调拨: {{ maxQuantity }} {{ selectedMaterial.unit }}</span>
          </div>
        </div>

        <div v-if="selectedMaterial?.has_individual_tracking" class="tracking-warning">
          ⚠️ 个体追踪物资请使用管理页逐项操作。
        </div>

        <div v-if="previewText" class="preview-box">
          <span class="preview-icon">📋</span>
          <span>{{ previewText }}</span>
        </div>

        <button class="btn-primary" @click="submit" :disabled="!canSubmit">
          确认调拨
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { toast } from '../utils/toast.js'
import { fetchWarehouses, fetchWarehouseDetail } from '../api/warehouses.js'
import { transfer } from '../api/transfer.js'

const props = defineProps({
  visible: Boolean,
  preselectedWarehouseId: Number,
})
const emit = defineEmits(['close', 'done'])

const warehouses = ref([])
const fromWarehouseId = ref(null)
const toWarehouseId = ref(null)
const selectedMaterialId = ref(null)
const fromMaterials = ref([])
const quantity = ref(1)
const submitting = ref(false)

const toWarehouseOptions = computed(() =>
  warehouses.value.filter(w => w.id !== fromWarehouseId.value)
)

const selectedMaterial = computed(() =>
  fromMaterials.value.find(m => m.id === selectedMaterialId.value)
)

const maxQuantity = computed(() => {
  if (!selectedMaterial.value) return 0
  return selectedMaterial.value.total_quantity || 0
})

const previewText = computed(() => {
  if (!selectedMaterial.value || !fromWarehouseId.value || !toWarehouseId.value || quantity.value < 1) return ''
  const fromWh = warehouses.value.find(w => w.id === fromWarehouseId.value)
  const toWh = warehouses.value.find(w => w.id === toWarehouseId.value)
  if (!fromWh || !toWh) return ''
  return `将 ${quantity.value} ${selectedMaterial.value.unit} ${selectedMaterial.value.name} 从 ${fromWh.name} 调拨到 ${toWh.name}`
})

const canSubmit = computed(() =>
  fromWarehouseId.value && toWarehouseId.value &&
  selectedMaterialId.value && selectedMaterial.value &&
  !selectedMaterial.value.has_individual_tracking &&
  quantity.value > 0 && quantity.value <= maxQuantity.value &&
  !submitting.value
)

async function loadWarehouses() {
  const res = await fetchWarehouses()
  if (res.ok) warehouses.value = res.data
}

async function loadFromMaterials() {
  if (!fromWarehouseId.value) {
    fromMaterials.value = []
    return
  }
  const res = await fetchWarehouseDetail(fromWarehouseId.value)
  if (res.ok) {
    fromMaterials.value = (res.data.materials || []).filter(
      m => m.sub_category === 'recyclable' && !m.has_individual_tracking
    )
  }
}

function onFromChange() {
  selectedMaterialId.value = null
  quantity.value = 1
  toWarehouseId.value = null
  loadFromMaterials()
}

function onMaterialChange() {
  quantity.value = 1
}

watch(() => props.visible, (v) => {
  if (v) {
    loadWarehouses()
    fromWarehouseId.value = props.preselectedWarehouseId || null
    toWarehouseId.value = null
    selectedMaterialId.value = null
    quantity.value = 1
    if (props.preselectedWarehouseId) {
      loadFromMaterials()
    }
  }
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  const res = await transfer({
    material_id: selectedMaterialId.value,
    from_warehouse_id: fromWarehouseId.value,
    to_warehouse_id: toWarehouseId.value,
    quantity: quantity.value,
  })
  submitting.value = false
  if (res.ok) {
    emit('done', res)
  } else {
    toast(res.msg, 'error')
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

.qty-row { display: flex; align-items: center; gap: 10px; }
.qty-input { flex: 1; }
.qty-hint { font-size: 0.78rem; color: #8e9aab; white-space: nowrap; }

.empty-hint { text-align: center; color: #8e9aab; padding: 20px; font-size: 0.88rem; }

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
