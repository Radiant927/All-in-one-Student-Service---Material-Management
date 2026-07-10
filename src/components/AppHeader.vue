<template>
  <header class="header">
    <div class="header-title">
      <div class="header-icon">📦</div>
      <h1>一站式物资管理系统</h1>
    </div>
    <div class="header-actions">
      <button class="btn-icon" @click="$emit('toggle-admin')" title="管理员设置">⚙️</button>
    </div>
  </header>
</template>

<script setup>
defineEmits(['toggle-admin'])
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
</style>
