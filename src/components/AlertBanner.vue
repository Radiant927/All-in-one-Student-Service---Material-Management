<template>
  <div class="alert-banner" v-if="visible">
    <span class="alert-icon">⚠️</span>
    <div class="alert-body">
      <span class="alert-title">库存预警：{{ criticalCount }} 种物资库存不足</span>
      <span class="alert-detail" v-if="topItems.length > 0">
        <template v-for="(item, idx) in topItems" :key="item.material_id">
          {{ item.icon }} {{ item.name }}（预计 {{ item.days_until_empty }} 天耗尽）<template v-if="idx < topItems.length - 1">、</template>
        </template>
      </span>
    </div>
    <button class="alert-action" @click="$emit('view-reports')">查看报表 →</button>
    <button class="alert-dismiss" @click="visible = false" title="关闭">✕</button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  alerts: { type: Array, default: () => [] },
  criticalCount: { type: Number, default: 0 },
  warningCount: { type: Number, default: 0 },
})
defineEmits(['view-reports'])

const visible = ref(true)

// Reset visibility when alerts update
watch(() => props.alerts, () => {
  visible.value = props.alerts.length > 0
})
</script>

<style scoped>
.alert-banner {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; margin-bottom: 6px;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1.5px solid #fde68a;
  border-radius: 16px;
  animation: bannerIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(245, 158, 11, 0.15);
}
@keyframes bannerIn {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}
.alert-icon {
  font-size: 22px; flex-shrink: 0;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.alert-body { flex: 1; min-width: 0; }
.alert-title { font-weight: 700; color: #92400e; font-size: 0.9rem; display: block; }
.alert-detail { font-size: 0.8rem; color: #a16207; display: block; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-action {
  padding: 8px 16px; border-radius: 20px; border: 1.5px solid #d97706;
  background: #fffbeb; color: #92400e; font-weight: 700;
  font-size: 0.82rem; cursor: pointer; white-space: nowrap;
  transition: all 0.3s; font-family: inherit;
}
.alert-action:hover { background: #fef3c7; box-shadow: 0 2px 8px rgba(217,119,6,0.2); }
.alert-dismiss {
  width: 28px; height: 28px; border-radius: 50%; border: none;
  background: transparent; cursor: pointer; font-size: 14px;
  color: #a16207; flex-shrink: 0;
  transition: all 0.3s;
}
.alert-dismiss:hover { background: #fde68a; color: #78350f; }

@media (max-width: 768px) {
  .alert-banner { flex-wrap: wrap; gap: 8px; }
  .alert-action { width: 100%; text-align: center; }
}
</style>
