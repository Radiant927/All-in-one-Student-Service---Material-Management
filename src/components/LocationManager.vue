<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">📍 储位管理</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>

        <div class="form-row">
          <select class="form-select" v-model="newLocation.warehouse_id">
            <option value="">选择仓库</option>
            <option v-for="wh in warehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
          </select>
        </div>
        <div class="form-row">
          <input class="form-input" v-model="newLocation.shelf" placeholder="货架号 (如 A)">
          <input class="form-input" v-model.number="newLocation.level" type="number" placeholder="层 (如 1)" min="1">
          <input class="form-input" v-model="newLocation.position" placeholder="位 (如 2)">
        </div>
        <button class="btn-primary" @click="addLocation" :disabled="!canAdd">添加储位</button>

        <div class="location-list">
          <div v-for="loc in allLocations" :key="loc.id" class="location-item">
            <span class="loc-code">{{ loc.full_code }}</span>
            <span class="loc-warehouse">{{ loc.warehouse_name }}</span>
            <button class="btn-delete" @click="removeLocation(loc.id)">🗑️</button>
          </div>
          <p v-if="allLocations.length === 0" class="empty">暂无储位</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { toast } from '../utils/toast.js'
import { fetchWarehouses, fetchAllLocations, createLocation, deleteLocation } from '../api/warehouses.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const warehouses = ref([])
const allLocations = ref([])

const newLocation = reactive({
  warehouse_id: '',
  shelf: '',
  level: 1,
  position: '',
})

const canAdd = computed(() =>
  newLocation.warehouse_id && newLocation.shelf.trim() && newLocation.level > 0
)

async function loadData() {
  const [whRes, locRes] = await Promise.all([fetchWarehouses(), fetchAllLocations()])
  if (whRes.ok) warehouses.value = whRes.data
  if (locRes.ok) allLocations.value = locRes.data
}

watch(() => props.visible, (v) => {
  if (v) loadData()
})

async function addLocation() {
  const res = await createLocation({
    warehouse_id: newLocation.warehouse_id,
    shelf: newLocation.shelf.trim(),
    level: newLocation.level,
    position: newLocation.position.trim(),
  })
  if (res.ok) {
    newLocation.shelf = ''
    newLocation.level = 1
    newLocation.position = ''
    await loadData()
  } else {
    toast(res.msg, 'error')
  }
}

async function removeLocation(id) {
  if (!confirm('确定删除此储位吗？')) return
  const res = await deleteLocation(id)
  if (res.ok) {
    await loadData()
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
  width: 92%; max-width: 480px; max-height: 80vh; overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18);
  transform: scale(0.92); transition: transform 0.25s;
}
.modal-overlay.active .modal-content { transform: scale(1); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-title { font-size: 1.15rem; font-weight: 700; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }
.form-row { display: flex; gap: 8px; margin-bottom: 12px; }
.form-input, .form-select {
  flex: 1; padding: 11px 14px; border-radius: 10px;
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
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }
.location-list { margin-top: 20px; }
.location-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: #f8fafc; margin-bottom: 8px; border: 1px solid #eef1f5;
}
.loc-code { font-weight: 700; color: #1a2332; flex: 1; }
.loc-warehouse { font-size: 0.78rem; color: #8e9aab; }
.btn-delete {
  background: none; border: none; cursor: pointer; font-size: 16px;
  padding: 4px 8px; border-radius: 6px; transition: all 0.2s;
}
.btn-delete:hover { background: #fef2f2; }
.empty { text-align: center; color: #8e9aab; padding: 20px; font-size: 0.88rem; }
</style>