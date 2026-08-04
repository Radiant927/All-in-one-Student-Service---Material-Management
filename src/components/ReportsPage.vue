<template>
  <div class="reports-page">
    <div class="reports-header">
      <button class="back-btn" @click="$emit('back')">← 返回</button>
      <h2 class="reports-title">📊 补货建议报表</h2>
      <div class="reports-controls">
        <select class="period-select" v-model.number="windowDays">
          <option :value="30">最近 30 天</option>
          <option :value="60">最近 60 天</option>
          <option :value="90">最近 90 天</option>
        </select>
        <button class="btn-export" @click="exportExcel">📥 导出 Excel</button>
        <button class="btn-email" @click="handleSendEmail" :disabled="sendingEmail">
          {{ sendingEmail ? '发送中...' : '📧 发送邮件' }}
        </button>
      </div>
    </div>

    <!-- Summary cards -->
    <div class="report-summary" v-if="reportData">
      <div class="summary-card critical">
        <span class="summary-num">{{ reportData.summary.critical_count }}</span>
        <span class="summary-label">🔴 紧急</span>
      </div>
      <div class="summary-card warning">
        <span class="summary-num">{{ reportData.summary.warning_count }}</span>
        <span class="summary-label">🟡 预警</span>
      </div>
      <div class="summary-card ok">
        <span class="summary-num">{{ reportData.summary.insufficient_data_count }}</span>
        <span class="summary-label">📊 数据不足</span>
      </div>
      <div class="summary-card total">
        <span class="summary-num">{{ reportData.summary.total_items }}</span>
        <span class="summary-label">📦 总计</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">正在分析消耗数据...</div>

    <!-- Table -->
    <div class="report-table-wrap" v-else-if="reportData && reportData.items.length > 0">
      <table class="report-table">
        <thead>
          <tr>
            <th>物资</th>
            <th>规格</th>
            <th class="col-num">当前库存</th>
            <th class="col-num">日均消耗</th>
            <th class="col-num">预计耗尽</th>
            <th class="col-num">建议补货</th>
            <th>状态</th>
            <th class="col-action">趋势</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in reportData.items" :key="item.material_id">
            <tr :class="rowClass(item)">
              <td class="col-name">{{ item.icon }} {{ item.name }}</td>
              <td class="col-spec">{{ item.spec || '-' }}</td>
              <td class="col-num">{{ item.current_stock }} {{ item.unit }}</td>
              <td class="col-num">{{ formatRate(item.daily_velocity) }}/天</td>
              <td class="col-num">{{ formatDays(item.days_until_empty) }}</td>
              <td class="col-num">
                <span v-if="item.suggested_restock_qty > 0" class="restock-qty">
                  {{ item.suggested_restock_qty }} {{ item.unit }}
                </span>
                <span v-else class="restock-none">-</span>
              </td>
              <td>
                <span class="status-badge" :class="item.status">{{ statusLabels[item.status] }}</span>
              </td>
              <td class="col-action">
                <button class="btn-trend" @click="toggleTrend(item.material_id)">
                  {{ expandedId === item.material_id ? '收起' : '趋势' }}
                </button>
              </td>
            </tr>
            <!-- Expanded trend row -->
            <tr v-if="expandedId === item.material_id" class="trend-row">
              <td colspan="8">
                <div class="trend-panel">
                  <div v-if="trendLoading" class="trend-loading">加载中...</div>
                  <div v-else-if="trendData" class="trend-chart">
                    <div class="trend-bars">
                      <div v-for="d in trendData.data" :key="d.month" class="trend-bar-col">
                        <div class="trend-bar" :style="{ height: barHeight(d.consumed, trendMax) }" :title="`${d.month}: ${d.consumed} ${trendData.unit}`"></div>
                        <span class="trend-label">{{ d.month.slice(5) }}月</span>
                        <span class="trend-val">{{ d.consumed }}</span>
                      </div>
                    </div>
                    <div class="trend-info">
                      月均消耗: {{ trendData.average_monthly }} {{ trendData.unit }} ·
                      总计: {{ trendData.total_consumed }} {{ trendData.unit }}
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-else-if="!loading" class="empty-state">
      <p>暂无报表数据</p>
      <p class="empty-hint">点击上方"发送邮件"可将报表发送给采购负责人</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { fetchRestockSuggestions, fetchConsumptionTrends, sendReportEmail } from '../api/reports.js'

defineEmits(['back'])
const props = defineProps({
  toast: { type: Function, default: null },
})

const loading = ref(true)
const reportData = ref(null)
const windowDays = ref(30)
const expandedId = ref(null)
const trendData = ref(null)
const trendLoading = ref(false)
const trendMax = ref(100)
const sendingEmail = ref(false)

const statusLabels = {
  critical: '🔴 紧急',
  warning: '🟡 预警',
  ok: '✅ 正常',
  insufficient_data: '📊 数据不足',
}

async function loadReport() {
  loading.value = true
  expandedId.value = null
  trendData.value = null
  const res = await fetchRestockSuggestions(windowDays.value)
  if (res.ok) reportData.value = res.data
  loading.value = false
}

function rowClass(item) {
  if (item.status === 'critical') return 'row-critical'
  if (item.status === 'warning') return 'row-warning'
  return ''
}

function formatRate(rate) {
  if (!rate || rate < 0.001) return '-'
  return rate.toFixed(1)
}

function formatDays(days) {
  if (days === null || days === undefined) return 'N/A'
  if (days >= 365) return Math.round(days / 365) + ' 年'
  return Math.round(days) + ' 天'
}

function barHeight(val, max) {
  if (max === 0) return '0%'
  return Math.max(4, (val / max) * 100) + '%'
}

async function toggleTrend(materialId) {
  if (expandedId.value === materialId) {
    expandedId.value = null
    trendData.value = null
    return
  }
  expandedId.value = materialId
  trendLoading.value = true
  trendData.value = null
  const res = await fetchConsumptionTrends(materialId, 3)
  if (res.ok) {
    trendData.value = res.data
    const maxVal = Math.max(...res.data.data.map(d => d.consumed), 1)
    trendMax.value = maxVal
  }
  trendLoading.value = false
}

function exportExcel() {
  const url = `/api/reports/export?format=excel&window_days=${windowDays.value}`
  window.open(url, '_blank')
}

async function handleSendEmail() {
  sendingEmail.value = true
  const res = await sendReportEmail()
  if (props.toast) {
    props.toast(res.msg || (res.ok ? '邮件发送成功' : '邮件发送失败'), res.ok ? 'success' : 'error')
  }
  sendingEmail.value = false
}

watch(windowDays, loadReport)
onMounted(loadReport)
</script>

<style scoped>
.reports-page {
  background: rgba(255,255,255,0.82); backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px; padding: 22px 26px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}

/* Header */
.reports-header { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.reports-title { font-size: 1.2rem; font-weight: 700; flex: 1; }
.back-btn {
  padding: 8px 16px; border-radius: 20px; border: 1.5px solid #dde4ed;
  background: #f8fafc; cursor: pointer; font-size: 0.85rem; font-weight: 600;
  color: #5a6b7d; transition: all 0.3s; font-family: inherit;
}
.back-btn:hover { border-color: #667eea; color: #667eea; }
.reports-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.period-select {
  padding: 8px 12px; border-radius: 10px; border: 1.5px solid #dde4ed;
  background: #f8fafc; font-size: 0.85rem; font-family: inherit;
  color: #1a2332; cursor: pointer; outline: none;
}
.btn-export, .btn-email {
  padding: 8px 16px; border-radius: 20px; border: 1.5px solid #dde4ed;
  background: #f8fafc; cursor: pointer; font-size: 0.85rem; font-weight: 600;
  color: #5a6b7d; transition: all 0.3s; font-family: inherit; white-space: nowrap;
}
.btn-export:hover { border-color: #22c55e; color: #16a34a; background: #f0fdf4; }
.btn-email:hover { border-color: #667eea; color: #4facfe; background: #eff6ff; }
.btn-email:disabled { opacity: 0.5; cursor: not-allowed; }

/* Summary */
.report-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }
.summary-card {
  padding: 16px 14px; border-radius: 14px; text-align: center;
  background: #f8fafc; border: 1.5px solid #e2e8f0;
  transition: transform 0.3s;
}
.summary-card:hover { transform: translateY(-2px); }
.summary-num { display: block; font-size: 1.6rem; font-weight: 800; }
.summary-label { display: block; font-size: 0.78rem; color: #5a6b7d; margin-top: 2px; }
.summary-card.critical .summary-num { color: #dc2626; }
.summary-card.warning .summary-num { color: #d97706; }
.summary-card.ok .summary-num { color: #6366f1; }
.summary-card.total .summary-num { color: #1a2332; }

/* Table */
.report-table-wrap { overflow-x: auto; }
.report-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
.report-table th {
  padding: 11px 12px; text-align: left; font-size: 0.78rem; font-weight: 700;
  color: #5a6b7d; border-bottom: 2px solid #e2e8f0; white-space: nowrap;
}
.report-table td {
  padding: 11px 12px; border-bottom: 1px solid #f1f5f9;
  color: #1a2332; white-space: nowrap;
}
.col-num { text-align: right; }
.col-spec { color: #8e9aab; font-size: 0.82rem; max-width: 140px; overflow: hidden; text-overflow: ellipsis; }
.col-action { text-align: center; }
.row-critical { background: #fef2f2; }
.row-warning { background: #fffbeb; }
.report-table tbody tr:hover { background: #f8fafc; }
.row-critical:hover { background: #fee2e2; }
.row-warning:hover { background: #fef3c7; }

.status-badge {
  padding: 4px 10px; border-radius: 12px; font-size: 0.78rem; font-weight: 700;
}
.status-badge.critical { background: #fee2e2; color: #dc2626; }
.status-badge.warning { background: #fef3c7; color: #d97706; }
.status-badge.ok { background: #d1fae5; color: #059669; }
.status-badge.insufficient_data { background: #e0e7ff; color: #4f46e5; }

.restock-qty { font-weight: 700; color: #dc2626; }
.restock-none { color: #ccd0d8; }

.btn-trend {
  padding: 5px 12px; border-radius: 12px; border: 1px solid #dde4ed;
  background: #fff; cursor: pointer; font-size: 0.78rem; font-weight: 600;
  color: #5a6b7d; transition: all 0.3s; font-family: inherit;
}
.btn-trend:hover { border-color: #667eea; color: #667eea; }

/* Trend panel */
.trend-row td { padding: 0; }
.trend-panel {
  padding: 16px 20px; background: #f8fafc; border-radius: 0 0 12px 12px;
}
.trend-bars { display: flex; gap: 28px; align-items: flex-end; height: 120px; justify-content: center; padding: 8px 0; }
.trend-bar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.trend-bar {
  width: 40px; border-radius: 8px 8px 0 0;
  background: linear-gradient(180deg, #667eea, #4facfe);
  min-height: 4px; transition: height 0.4s ease;
}
.trend-label { font-size: 0.72rem; color: #8e9aab; }
.trend-val { font-size: 0.78rem; font-weight: 700; color: #1a2332; }
.trend-info { text-align: center; margin-top: 10px; font-size: 0.8rem; color: #5a6b7d; }
.trend-loading { text-align: center; padding: 20px; color: #8e9aab; }

.loading-state, .empty-state { text-align: center; padding: 40px; color: #8e9aab; }
.empty-hint { font-size: 0.82rem; margin-top: 6px; }

@media (max-width: 768px) {
  .reports-page { padding: 16px; }
  .report-summary { grid-template-columns: repeat(2, 1fr); }
  .reports-header { flex-direction: column; align-items: flex-start; }
  .reports-controls { width: 100%; justify-content: flex-start; }
  .trend-bars { gap: 16px; }
  .trend-bar { width: 30px; }
}
</style>
