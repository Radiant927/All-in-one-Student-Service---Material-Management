<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">📤 借出 - {{ material?.icon }} {{ material?.name }}</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="form-group">
          <label class="form-label">借用人姓名</label>
          <input class="form-input" v-model="borrower" placeholder="请输入借用人姓名" @keydown.enter="confirm" ref="inputRef">
        </div>
        <div v-if="material?.hasIndividualTracking" class="form-group">
          <label class="form-label">遥控器代号</label>
          <select class="form-select" v-model="itemCode">
            <option v-if="availableItems.length === 0" value="">无可用遥控器</option>
            <option v-for="item in availableItems" :key="item.code" :value="item.code">{{ item.code }}</option>
          </select>
        </div>
        <div v-else class="form-group">
          <label class="form-label">借用数量</label>
          <select class="form-select" v-model.number="quantity">
            <option v-for="n in remaining" :key="n" :value="n">{{ n }} 个</option>
          </select>
        </div>
        <WarehouseSelector v-model="warehouseSelection" />
        <button class="btn-primary" @click="confirm">确认借出</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import WarehouseSelector from './WarehouseSelector.vue'

const props = defineProps({
  visible: Boolean,
  material: Object,
  remaining: Number,
  availableItems: Array
})

const emit = defineEmits(['close', 'confirm'])

const borrower = ref('')
const itemCode = ref('')
const quantity = ref(1)
const inputRef = ref(null)
const warehouseSelection = ref({ warehouse_id: null, location_id: null })

watch(() => props.visible, (v) => {
  if (v) {
    borrower.value = ''
    itemCode.value = ''
    quantity.value = 1
    warehouseSelection.value = { warehouse_id: null, location_id: null }
    setTimeout(() => inputRef.value?.focus(), 200)
  }
})

function confirm() {
  emit('confirm', {
    materialId: props.material?.id,
    borrower: borrower.value,
    itemCode: itemCode.value,
    quantity: quantity.value,
    warehouseId: warehouseSelection.value.warehouse_id,
  })
}
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
.form-input, .form-select {
  width: 100%; padding: 11px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.93rem;
  color: #1a2332; background: #f8fafc; transition: all 0.3s; outline: none;
}
.form-input:focus, .form-select:focus {
  border-color: #667eea; background: #fff;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-primary:active { transform: scale(0.96); }
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }
</style>
