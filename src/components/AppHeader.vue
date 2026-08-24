<template>
  <header class="header">
    <div class="header-title">
      <div class="header-icon">📦</div>
      <h1>一站式物资管理系统</h1>
    </div>
    <div class="header-actions">
      <button class="btn-icon" @click="$emit('toggle-warehouse')" title="仓库视图">🏗️</button>
      <button class="btn-icon" @click="$emit('toggle-archive')" title="物资档案">📋</button>
      <button class="btn-icon" @click="$emit('toggle-import')" title="导入数据">📥</button>
      <button class="btn-icon" @click="$emit('toggle-applications')" title="借用申请">📝</button>
      <button class="btn-icon" @click="$emit('toggle-reports')" title="补货报表">
        📊
        <span v-if="alertBadge > 0" class="badge-dot">{{ alertBadge }}</span>
      </button>
      <button class="btn-icon" @click="$emit('toggle-admin')" title="管理员设置">⚙️</button>
    </div>
  </header>
</template>

<script setup>
defineEmits(['toggle-admin', 'toggle-archive', 'toggle-import', 'toggle-warehouse', 'toggle-reports', 'toggle-applications'])
defineProps({ alertBadge: { type: Number, default: 0 } })
</script>

<style scoped>
.header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 28px;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}
.header-title { display: flex; align-items: center; gap: 12px; }
.header-icon {
  width: 42px; height: 42px; border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #4facfe);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; color: #fff;
  box-shadow: 0 4px 12px rgba(102,126,234,0.35);
}
.header h1 {
  font-size: 1.45rem; font-weight: 700;
  background: linear-gradient(135deg, #667eea, #2d8de8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-actions { display: flex; gap: 10px; }
.btn-icon {
  width: 42px; height: 42px; border-radius: 12px;
  border: 1.5px solid #dde4ed;
  background: rgba(255,255,255,0.7);
  cursor: pointer; font-size: 19px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s; color: #5a6b7d;
}
.btn-icon:hover {
  background: #fff; border-color: #667eea;
  color: #667eea; box-shadow: 0 4px 14px rgba(102,126,234,0.2);
  transform: translateY(-1px);
}
.btn-icon { position: relative; }
.badge-dot {
  position: absolute; top: -5px; right: -6px;
  min-width: 18px; height: 18px; border-radius: 9px;
  background: #ef4444; color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; box-shadow: 0 2px 6px rgba(239,68,68,0.4);
}
</style>
