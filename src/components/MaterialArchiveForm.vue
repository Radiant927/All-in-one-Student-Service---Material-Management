<template>
  <Teleport to="body">
    <div class="modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">{{ isEdit ? '✏️ 编辑物资' : '➕ 新增物资' }}</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="form-group">
          <label class="form-label">品名 <span class="required">*</span></label>
          <input class="form-input" v-model="form.name" placeholder="请输入物资名称">
        </div>
        <div class="form-group">
          <label class="form-label">规格</label>
          <input class="form-input" v-model="form.spec" placeholder="如: 0.5mm 黑色">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">单位</label>
            <input class="form-input" v-model="form.unit" placeholder="个/支/箱/包">
          </div>
          <div class="form-group">
            <label class="form-label">图标</label>
            <input class="form-input" v-model="form.icon" placeholder="📦">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">物资分类</label>
          <select class="form-select" v-model="form.category">
            <option value="consumable">消耗性物资</option>
            <option value="durable">固定性物资</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">流转类型</label>
          <select class="form-select" v-model="form.sub_category">
            <option value="new_consumable">全新消耗品</option>
            <option value="recyclable">可循环物资</option>
            <option value="direct_consumption">直接消耗品</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">预警阈值</label>
          <input class="form-input" v-model.number="form.low_stock_threshold" type="number" min="0">
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="form.has_individual_tracking">
            个体追踪（每个物资有独立代号，如遥控器）
          </label>
        </div>
        <button class="btn-primary" @click="submit" :disabled="!form.name.trim()">
          {{ isEdit ? '保存修改' : '创建物资' }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  material: Object,
})

const emit = defineEmits(['close', 'submit'])

const isEdit = computed(() => !!props.material)

const form = reactive({
  name: '',
  spec: '',
  unit: '个',
  category: 'consumable',
  sub_category: 'direct_consumption',
  has_individual_tracking: false,
  low_stock_threshold: 5,
  icon: '📦',
})

watch(() => props.visible, (v) => {
  if (v) {
    if (props.material) {
      Object.assign(form, {
        name: props.material.name || '',
        spec: props.material.spec || '',
        unit: props.material.unit || '个',
        category: props.material.category || 'consumable',
        sub_category: props.material.sub_category || 'direct_consumption',
        has_individual_tracking: props.material.has_individual_tracking || false,
        low_stock_threshold: props.material.low_stock_threshold || 5,
        icon: props.material.icon || '📦',
      })
    } else {
      Object.assign(form, {
        name: '', spec: '', unit: '个', category: 'consumable',
        sub_category: 'direct_consumption', has_individual_tracking: false,
        low_stock_threshold: 5, icon: '📦',
      })
    }
  }
})

function submit() {
  emit('submit', { ...form })
}
</script>

<script>
import { computed } from 'vue'
export default { inheritAttrs: false }
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
  width: 92%; max-width: 460px; max-height: 90vh; overflow-y: auto;
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
.form-group { margin-bottom: 14px; }
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
.form-row { display: flex; gap: 10px; }
.form-row .form-group { flex: 1; }
.checkbox-group label { display: flex; align-items: center; gap: 8px; font-size: 0.88rem; cursor: pointer; color: #1a2332; }
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s; margin-top: 6px;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }
</style>