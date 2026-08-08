<template>
  <section class="applications-page">
    <div class="page-header">
      <div>
        <button class="back-button" @click="$emit('back')">← 返回</button>
        <h2>借用申请审核</h2>
        <p>审核后只预留库存，现场确认领取时才扣减。</p>
      </div>
      <button class="primary-button" @click="loadApplications">刷新</button>
    </div>

    <div class="scan-terminal">
      <strong>扫码终端</strong>
      <input
        ref="scanInput"
        v-model.trim="scanPayload"
        placeholder="扫码枪输入或粘贴 MATERIAL:/ITEM: 二维码"
        @keyup.enter="handleScan"
      >
      <button @click="handleScan" :disabled="scanning">识别</button>
      <span v-if="scanResult" class="scan-result">
        {{ scanResult.material.name }} · 可申请 {{ scanResult.material.available_quantity }}
      </span>
    </div>

    <div class="filters">
      <button
        v-for="option in statusOptions"
        :key="option.value"
        :class="{ active: status === option.value }"
        @click="status = option.value; loadApplications()"
      >{{ option.label }}</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="empty">正在加载…</p>
    <p v-else-if="rows.length === 0" class="empty">暂无符合条件的借用申请</p>

    <div v-else class="application-list">
      <article v-for="item in rows" :key="item.id" class="application-card">
        <div class="application-main">
          <div class="title-row">
            <strong>{{ item.material_name }}</strong>
            <span class="status" :class="item.status">{{ statusLabel(item.status) }}</span>
          </div>
          <p>{{ item.applicant_name }}（{{ item.student_no || '无学号' }}）申请 {{ item.quantity }} 件</p>
          <p v-if="item.item_code">个体代号：{{ item.item_code }}</p>
          <p v-if="item.purpose">用途：{{ item.purpose }}</p>
          <p v-if="item.expires_at">预留截止：{{ formatTime(item.expires_at) }}</p>
        </div>
        <div class="actions">
          <button v-if="item.status === 'submitted'" class="approve" @click="approve(item)">通过</button>
          <button v-if="item.status === 'submitted'" class="reject" @click="reject(item)">拒绝</button>
          <button v-if="item.status === 'approved'" class="pickup" @click="pickup(item)">确认领取</button>
          <button v-if="item.status === 'return_pending'" class="return" @click="returnItem(item)">归还验收</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import {
  approveBorrowApplication,
  confirmPickup,
  confirmReturn,
  fetchBorrowApplications,
  rejectBorrowApplication,
  resolveScan,
} from '../api/borrowApplications.js'
import { applicationStatusLabel } from '../constants/applicationStatus.js'

const props = defineProps({ toast: Function })
defineEmits(['back'])

const rows = ref([])
const status = ref('')
const loading = ref(false)
const error = ref('')
const scanPayload = ref('')
const scanResult = ref(null)
const scanning = ref(false)
const scanInput = ref(null)

const statusOptions = [
  { value: '', label: '全部' },
  { value: 'submitted', label: '待审核' },
  { value: 'approved', label: '待领取' },
  { value: 'return_pending', label: '待验收' },
  { value: 'returned', label: '已归还' },
]

function statusLabel(value) { return applicationStatusLabel(value) }
function formatTime(value) { return new Date(value).toLocaleString('zh-CN') }
function operationKey(prefix, id) {
  const suffix = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
  return `${prefix}-${id}-${suffix}`
}

async function loadApplications() {
  loading.value = true
  error.value = ''
  const result = await fetchBorrowApplications({ status: status.value })
  loading.value = false
  if (!result.ok) {
    error.value = result.msg || '加载失败，请先在管理员设置中登录'
    rows.value = []
    return
  }
  rows.value = result.data?.rows || []
}

async function approve(item) {
  const note = window.prompt('审核备注（可留空）', '')
  if (note === null) return
  const result = await approveBorrowApplication(item.id, note)
  props.toast?.(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) loadApplications()
}

async function reject(item) {
  const note = window.prompt('请输入拒绝原因', '')
  if (note === null) return
  const result = await rejectBorrowApplication(item.id, note)
  props.toast?.(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) loadApplications()
}

async function pickup(item) {
  if (!window.confirm(`确认 ${item.applicant_name} 已领取 ${item.material_name}？`)) return
  const result = await confirmPickup(item.id, operationKey('pickup', item.id), item.warehouse_id)
  props.toast?.(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) loadApplications()
}

async function returnItem(item) {
  if (!window.confirm(`确认 ${item.material_name} 已验收并归还入库？`)) return
  const result = await confirmReturn(item.id, operationKey('return', item.id), item.warehouse_id)
  props.toast?.(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) loadApplications()
}

async function handleScan() {
  if (!scanPayload.value) return
  scanning.value = true
  const result = await resolveScan(scanPayload.value)
  scanning.value = false
  if (!result.ok) {
    props.toast?.(result.msg, 'error')
    scanResult.value = null
    return
  }
  scanResult.value = result.data
  props.toast?.('二维码识别成功', 'success')
  scanPayload.value = ''
  scanInput.value?.focus()
}

onMounted(loadApplications)
</script>

<style scoped>
.applications-page { background:#fff; border-radius:20px; padding:24px; margin-top:18px; box-shadow:0 4px 24px rgba(0,0,0,.07); }
.page-header,.scan-terminal,.application-card,.title-row,.actions,.filters { display:flex; align-items:center; gap:12px; }
.page-header { justify-content:space-between; align-items:flex-start; }
.page-header h2 { margin:8px 0 4px; }.page-header p,.application-card p { color:#64748b; margin:5px 0; }
.back-button { border:0; background:none; color:#4f46e5; cursor:pointer; }.primary-button,.scan-terminal button { background:#4f46e5; color:#fff; border:0; border-radius:9px; padding:9px 16px; }
.scan-terminal { margin:20px 0; padding:14px; background:#f8fafc; border-radius:12px; flex-wrap:wrap; }
.scan-terminal input { flex:1; min-width:260px; border:1px solid #cbd5e1; border-radius:9px; padding:10px; }.scan-result { color:#15803d; }
.filters { flex-wrap:wrap; margin-bottom:16px; }.filters button { border:1px solid #cbd5e1; background:#fff; border-radius:999px; padding:7px 14px; cursor:pointer; }.filters button.active { color:#fff; background:#4f46e5; border-color:#4f46e5; }
.application-list { display:grid; gap:12px; }.application-card { justify-content:space-between; border:1px solid #e2e8f0; border-radius:14px; padding:16px; }.application-main { flex:1; }.title-row { justify-content:space-between; }
.status { font-size:12px; border-radius:999px; padding:4px 9px; background:#e2e8f0; }.status.submitted { background:#fef3c7; }.status.approved { background:#dbeafe; }.status.return_pending { background:#ede9fe; }.status.returned { background:#dcfce7; }
.actions { flex-wrap:wrap; }.actions button { border:0; border-radius:8px; padding:8px 12px; color:#fff; cursor:pointer; }.approve,.pickup { background:#2563eb; }.reject { background:#dc2626; }.return { background:#16a34a; }
.empty { text-align:center; color:#64748b; padding:32px; }.error { color:#dc2626; background:#fef2f2; padding:12px; border-radius:9px; }
@media (max-width:700px) { .application-card { align-items:flex-start; flex-direction:column; }.page-header { flex-direction:column; } }
</style>
