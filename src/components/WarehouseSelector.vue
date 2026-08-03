<template>
  <div class="warehouse-selector">
    <div class="form-group">
      <label class="form-label">{{ label || '仓库 / 储位' }}</label>
      <select class="form-select" v-model="selectedWarehouseId" @change="onWarehouseChange">
        <option value="">选择仓库</option>
        <option v-for="wh in warehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
      </select>
    </div>
    <div class="form-group" v-if="showLocation">
      <select class="form-select" v-model="selectedLocationId">
        <option value="">选择储位（可选）</option>
        <option v-for="loc in filteredLocations" :key="loc.id" :value="loc.id">
          {{ loc.full_code }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchWarehouses, fetchLocations } from '../api/warehouses.js'

const props = defineProps({
  label: String,
  modelValue: Object,
  showLocation: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const warehouses = ref([])
const locations = ref([])
const selectedWarehouseId = ref('')
const selectedLocationId = ref('')

onMounted(async () => {
  const res = await fetchWarehouses()
  if (res.ok) warehouses.value = res.data
})

const filteredLocations = computed(() =>
  locations.value.filter(l => l.warehouse_id === selectedWarehouseId.value)
)

watch([selectedWarehouseId, selectedLocationId], () => {
  emit('update:modelValue', {
    warehouse_id: selectedWarehouseId.value || null,
    location_id: selectedLocationId.value || null,
  })
})

async function onWarehouseChange() {
  selectedLocationId.value = ''
  if (selectedWarehouseId.value) {
    const res = await fetchLocations(selectedWarehouseId.value)
    if (res.ok) locations.value = res.data
  }
}
</script>

<style scoped>
.warehouse-selector { display: flex; gap: 10px; }
.warehouse-selector .form-group { flex: 1; margin-bottom: 16px; }
.form-label { display: block; font-size: 0.84rem; font-weight: 600; color: #5a6b7d; margin-bottom: 6px; }
.form-select {
  width: 100%; padding: 11px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.93rem;
  color: #1a2332; background: #f8fafc; transition: all 0.3s; outline: none;
}
.form-select:focus {
  border-color: #667eea; background: #fff;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}
</style>