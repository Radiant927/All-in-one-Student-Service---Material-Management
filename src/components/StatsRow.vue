<template>
  <section class="stats-row">
    <div class="stat-tile">
      <div class="stat-icon blue">📦</div>
      <div>
        <div class="stat-label">物资种类</div>
        <div class="stat-value">{{ totalTypes }} 种</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon orange">🔧</div>
      <div>
        <div class="stat-label">固定性物资</div>
        <div class="stat-value">{{ durableCount }} 件</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon blue">📦</div>
      <div>
        <div class="stat-label">消耗性物资</div>
        <div class="stat-value">{{ consumableCount }} 件</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon green">✅</div>
      <div>
        <div class="stat-label">可借用</div>
        <div class="stat-value">{{ availableCount }} 件</div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  totalTypes: Number,
  durableCount: Number,
  consumableCount: Number,
  availableCount: Number
})
</script>

<style scoped>
.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
.stat-tile {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 16px;
  padding: 18px 20px; display: flex; align-items: center; gap: 14px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  transition: all 0.3s;
}
.stat-tile:hover { transform: translateY(-2px); box-shadow: 0 16px 48px rgba(0,0,0,0.13); }
.stat-icon {
  width: 46px; height: 46px; border-radius: 14px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
}
.stat-icon.blue { background: linear-gradient(135deg, #e0e7ff, #c7d2fe); color: #667eea; }
.stat-icon.orange { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #d97706; }
.stat-icon.green { background: linear-gradient(135deg, #d1fae5, #a7f3d0); color: #059669; }
.stat-label { font-size: 0.82rem; color: #5a6b7d; margin-bottom: 2px; }
.stat-value { font-size: 1.55rem; font-weight: 700; color: #1a2332; }

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .stat-tile { padding: 12px; gap: 8px; }
  .stat-icon { width: 36px; height: 36px; font-size: 17px; border-radius: 10px; }
  .stat-value { font-size: 1.15rem; }
}
</style>
