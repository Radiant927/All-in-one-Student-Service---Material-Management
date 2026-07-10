<template>
  <div class="material-card" :class="[cardAccentClass]">
    <span class="card-type-badge" :class="typeBadgeClass">{{ typeBadgeText }}</span>
    <div class="card-icon-circle" :class="iconAccentClass">{{ material.icon }}</div>
    <div class="card-title">{{ material.name }}</div>

    <div class="card-progress-wrap">
      <div class="card-progress-bar">
        <div class="card-progress-fill" :class="[fillClass, { warning: isWarning }]" :style="{ width: percent + '%' }"></div>
      </div>
    </div>

    <div class="card-quantities">
      <div class="quantity-item">
        <div class="quantity-number remaining">{{ remaining }}</div>
        <div class="quantity-label">剩余数量</div>
      </div>
      <div class="quantity-divider"></div>
      <div class="quantity-item">
        <div class="quantity-number borrowed">{{ borrowed }}</div>
        <div class="quantity-label">已借出数量</div>
      </div>
    </div>

    <div class="low-stock-badge" :class="{ visible: isLowStock || isOut }">
      {{ isOut ? '❌ 已全部借出' : '⚠️ 库存不足' }}
    </div>

    <div class="card-actions">
      <button class="btn btn-borrow" :disabled="isOut" @click="$emit('borrow', material.id)">
        {{ isOut ? '已借完' : '📤 借出' }}
      </button>
      <button class="btn btn-return" :disabled="borrowed === 0" @click="$emit('return', material.id)">
        {{ borrowed === 0 ? '无需归还' : '📥 归还' }}
      </button>
      <button
        v-if="material.hasIndividualTracking"
        class="btn btn-manage"
        @click="$emit('manage', material.id)"
      >📋 管理</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  material: Object,
  remaining: Number,
  borrowed: Number,
  total: Number
})

defineEmits(['borrow', 'return', 'manage'])

const accents = ['accent-1', 'accent-2', 'accent-3', 'accent-4']
const cardAccents = ['card-accent-1', 'card-accent-2', 'card-accent-3', 'card-accent-4']
const idx = (props.material.colorIdx || 0) % 4

const iconAccentClass = computed(() => accents[idx])
const cardAccentClass = computed(() => cardAccents[idx])
const fillClass = computed(() => accents[idx])

const typeBadgeClass = computed(() =>
  props.material.type === 'durable' ? 'badge-durable' : 'badge-consumable'
)
const typeBadgeText = computed(() =>
  props.material.type === 'durable' ? '固定' : '消耗'
)

const percent = computed(() =>
  props.total > 0 ? Math.round((props.borrowed / props.total) * 100) : 0
)

const isLowStock = computed(() =>
  props.remaining <= props.material.lowStockThreshold && props.remaining > 0
)
const isOut = computed(() => props.remaining === 0)
const isWarning = computed(() => props.remaining <= props.material.lowStockThreshold || percent.value > 80)
</script>

<style scoped>
.material-card {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px;
  padding: 28px 24px 22px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  transition: all 0.3s;
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; align-items: center;
}
.material-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  transition: height 0.3s;
}
.material-card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.13); }
.material-card:hover::before { height: 6px; }
.material-card.card-accent-1::before { background: linear-gradient(90deg, #667eea, #4facfe); }
.material-card.card-accent-2::before { background: linear-gradient(90deg, #4facfe, #667eea); }
.material-card.card-accent-3::before { background: linear-gradient(90deg, #43e97b, #4facfe); }
.material-card.card-accent-4::before { background: linear-gradient(90deg, #f59e0b, #f97316); }

.card-type-badge {
  position: absolute; top: 14px; right: 14px;
  font-size: 0.7rem; font-weight: 700; padding: 4px 11px;
  border-radius: 10px; z-index: 2;
}
.badge-durable { background: linear-gradient(135deg, #ede9fe, #ddd6fe); color: #7c3aed; }
.badge-consumable { background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #2563eb; }

.card-icon-circle {
  width: 80px; height: 80px; border-radius: 50%; margin-bottom: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 38px; position: relative; z-index: 1;
  box-shadow: 0 8px 28px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}
.material-card:hover .card-icon-circle { transform: scale(1.06); }
.card-icon-circle.accent-1 { background: linear-gradient(135deg, #667eea, #764ba2); }
.card-icon-circle.accent-2 { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.card-icon-circle.accent-3 { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.card-icon-circle.accent-4 { background: linear-gradient(135deg, #f59e0b, #f97316); }

.card-title { font-size: 1.2rem; font-weight: 700; color: #1a2332; margin-bottom: 16px; }

.card-progress-wrap { width: 100%; margin-bottom: 14px; }
.card-progress-bar { width: 100%; height: 10px; border-radius: 10px; background: #e8ecf1; overflow: hidden; }
.card-progress-fill { height: 100%; border-radius: 10px; transition: width 0.6s; position: relative; }
.card-progress-fill.accent-1 { background: linear-gradient(90deg, #667eea, #4facfe); }
.card-progress-fill.accent-2 { background: linear-gradient(90deg, #4facfe, #667eea); }
.card-progress-fill.accent-3 { background: linear-gradient(90deg, #43e97b, #4facfe); }
.card-progress-fill.accent-4 { background: linear-gradient(90deg, #f59e0b, #f97316); }
.card-progress-fill.warning { background: linear-gradient(90deg, #f59e0b, #ef4444); }
.card-progress-fill::after {
  content: ''; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent);
  animation: shimmer 2.2s ease-in-out infinite;
}
@keyframes shimmer { 0% { left: -60%; } 100% { left: 120%; } }

.card-quantities { width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.quantity-item { text-align: center; flex: 1; }
.quantity-number { font-size: 1.65rem; font-weight: 800; }
.quantity-number.remaining { color: #4c63d2; }
.quantity-number.borrowed { color: #5a6b7d; }
.quantity-label { font-size: 0.76rem; color: #8e9aab; margin-top: 1px; }
.quantity-divider { width: 1px; height: 34px; background: #e0e5ec; border-radius: 1px; }

.low-stock-badge {
  display: none; align-items: center; gap: 5px;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  color: #dc2626; font-size: 0.78rem; font-weight: 600;
  padding: 5px 14px; border-radius: 20px; margin-bottom: 10px;
  border: 1px solid #fecaca;
}
.low-stock-badge.visible { display: flex; animation: pulseBadge 1.6s ease-in-out infinite; }
@keyframes pulseBadge { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }

.card-actions { display: flex; gap: 10px; width: 100%; margin-top: 6px; }
.btn {
  flex: 1; padding: 11px 0; border-radius: 25px; border: none;
  font-size: 0.9rem; font-weight: 600; cursor: pointer;
  transition: all 0.3s;
}
.btn:active { transform: scale(0.95); }
.btn-borrow {
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; box-shadow: 0 4px 14px rgba(102,126,234,0.3);
}
.btn-borrow:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-2px); }
.btn-borrow:disabled { background: #ccd0d8; color: #99a0ab; cursor: not-allowed; box-shadow: none; transform: none; }
.btn-return {
  background: transparent; color: #667eea;
  border: 2px solid #667eea;
}
.btn-return:hover { background: rgba(102,126,234,0.06); transform: translateY(-2px); }
.btn-return:disabled { border-color: #ccd0d8; color: #b0b7c3; cursor: not-allowed; background: transparent; transform: none; }
.btn-manage {
  flex: 0.5; background: transparent; color: #2cc45e;
  border: 2px solid #43e97b; font-size: 0.82rem;
}
.btn-manage:hover { background: rgba(67,233,123,0.08); transform: translateY(-2px); }

@media (max-width: 768px) {
  .material-card { padding: 22px 18px 18px; }
  .card-icon-circle { width: 64px; height: 64px; font-size: 30px; }
  .card-title { font-size: 1.05rem; }
  .quantity-number { font-size: 1.35rem; }
}
</style>
