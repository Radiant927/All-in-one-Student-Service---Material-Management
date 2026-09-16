<template>
  <div class="stocktake-page">
    <div class="page-head">
      <button class="btn-back" @click="$emit('back')">← 返回</button>
      <div class="title-block">
        <h2>📋 库存盘点</h2>
        <small>按仓库和储位核对，个体物资请逐个扫码</small>
      </div>
      <button v-if="!current" class="btn-primary" :disabled="loading" @click="openCreate">＋ 发起盘点</button>
    </div>

    <div v-if="!current && !creating" class="st-list">
      <div v-if="list.length === 0 && !loading" class="empty">
        还没有盘点记录，点击「发起盘点」开始第一次清点。
      </div>
      <button v-for="stocktake in list" :key="stocktake.id" class="st-card" @click="openDetail(stocktake.id)">
        <div class="st-card-top">
          <span class="st-id">盘点单 #{{ stocktake.id }}</span>
          <span class="st-status" :class="stocktake.status">{{ statusLabel(stocktake.status) }}</span>
        </div>
        <div class="st-card-meta">
          <span>📅 {{ formatTime(stocktake.created_at) }}</span>
          <span v-if="stocktake.note">📝 {{ stocktake.note }}</span>
        </div>
        <div class="st-card-stats">
          <span>进度 <b>{{ stocktake.counted_count || 0 }}/{{ stocktake.entries_count }}</b></span>
          <span v-if="stocktake.discrepancy_count > 0" class="warn">⚠️ 差异 <b>{{ stocktake.discrepancy_count }}</b> 项</span>
          <span v-else class="muted">暂无已确认差异</span>
        </div>
      </button>
    </div>

    <div v-if="creating" class="st-create panel">
      <h3>发起盘点</h3>
      <p class="hint">系统会冻结当前账面快照。同一时间只能进行一张盘点单。</p>
      <textarea v-model="newNote" maxlength="500" placeholder="盘点备注（可选），如：月底例行盘点"></textarea>
      <div class="actions-right">
        <button class="btn-ghost" @click="creating = false">取消</button>
        <button class="btn-primary" :disabled="loading" @click="doCreate">确认发起</button>
      </div>
    </div>

    <div v-if="current" class="st-detail">
      <div class="detail-head">
        <button class="btn-back" @click="closeDetail">← 返回列表</button>
        <div class="title-block">
          <h3>盘点单 #{{ current.id }}</h3>
          <small>{{ current.note || '无备注' }}</small>
        </div>
        <div v-if="current.status === 'in_progress'" class="detail-actions">
          <button class="btn-danger-soft" :disabled="loading" @click="doCancel">取消盘点</button>
          <button class="btn-ghost" :disabled="loading || current.pending_count > 0" @click="doComplete(false)">完成盘点</button>
          <button class="btn-success" :disabled="loading || current.pending_count > 0" @click="doComplete(true)">完成并修正库存</button>
        </div>
      </div>

      <div class="progress-card">
        <div class="progress-copy">
          <b>已完成 {{ current.counted_count }}/{{ current.entries_count }} 项</b>
          <span v-if="current.pending_count > 0">还有 {{ current.pending_count }} 项需要确认</span>
          <span v-else class="ok">所有项目均已清点，可完成盘点</span>
        </div>
        <div class="progress-track"><i :style="{ width: progressPercent + '%' }"></i></div>
      </div>

      <div class="detail-summary">
        <span>账面总数 <b>{{ current.total_book }}</b></span>
        <span>已确认实盘 <b>{{ current.total_actual }}</b></span>
        <span :class="current.total_difference === 0 ? 'ok' : 'warn'">
          差异 <b>{{ signed(current.total_difference) }}</b>
        </span>
      </div>

      <div class="toolbar">
        <div class="filters">
          <button v-for="option in filters" :key="option.value" :class="{ active: filter === option.value }" @click="filter = option.value">
            {{ option.label }}
          </button>
        </div>
        <button v-if="current.status === 'in_progress'" class="btn-ghost" @click="showSurplus = !showSurplus">＋ 添加盘盈项</button>
      </div>

      <form v-if="showSurplus && current.status === 'in_progress'" class="surplus-form panel" @submit.prevent="addSurplus">
        <select v-model.number="surplus.material_id" required>
          <option :value="null" disabled>选择物资</option>
          <option v-for="material in materials" :key="material.id" :value="material.id">{{ material.name }}</option>
        </select>
        <select v-model.number="surplus.warehouse_id" required>
          <option :value="null" disabled>选择仓库</option>
          <option v-for="warehouse in warehouses" :key="warehouse.id" :value="warehouse.id">{{ warehouse.name }}</option>
        </select>
        <select v-model.number="surplus.location_id">
          <option :value="null">未指定储位</option>
          <option v-for="location in surplusLocations" :key="location.id" :value="location.id">{{ location.full_code }}</option>
        </select>
        <input v-model.number="surplus.actual_quantity" type="number" min="0" step="1" required placeholder="实际数量">
        <button class="btn-primary" :disabled="loading">加入</button>
      </form>

      <div class="entry-list">
        <article v-for="entry in filteredEntries" :key="entry.id" class="entry-card" :class="{ counted: entry.counted, discrepancy: entry.counted && entry.difference !== 0 }">
          <div class="entry-main">
            <div class="entry-name">
              <b>{{ entry.material_name }}</b>
              <small>{{ entry.material_spec }}</small>
            </div>
            <div class="entry-location">
              <span>{{ entry.warehouse_name }}</span>
              <small>{{ entry.location_code }}</small>
            </div>
            <div class="metric"><small>账面</small><b>{{ entry.book_quantity }}</b></div>
            <div class="metric"><small>实际</small><b>{{ entry.counted || entry.is_individual ? entry.actual_quantity : '待录入' }}</b></div>
            <div class="metric" :class="entry.difference === 0 ? 'ok' : (entry.difference > 0 ? 'pos' : 'neg')">
              <small>差异</small><b>{{ entry.counted ? signed(entry.difference) : '—' }}</b>
            </div>
            <span class="count-badge" :class="entry.counted ? 'done' : 'pending'">{{ entry.counted ? '已确认' : '待清点' }}</span>
          </div>

          <div v-if="current.status === 'in_progress' && !entry.is_individual" class="bulk-editor">
            <label>实际数量</label>
            <input type="number" min="0" step="1" :value="entry.actual_quantity ?? ''" placeholder="请输入非负整数" @change="updateBulkEntry(entry, $event)">
            <span>录入后自动确认该项</span>
          </div>

          <div v-if="entry.is_individual" class="individual-editor">
            <div class="scan-row" v-if="current.status === 'in_progress'">
              <input v-model="scanInputs[entry.id]" placeholder="扫描二维码或输入唯一编号" @keyup.enter="scanItem(entry)">
              <button class="btn-primary" :disabled="loading || !scanInputs[entry.id]?.trim()" @click="scanItem(entry)">扫描</button>
              <button class="btn-success" :disabled="loading" @click="confirmIndividual(entry)">确认本储位清点完成</button>
            </div>
            <div class="scan-summary">
              <span>已扫 <b>{{ entry.scanned_count }}</b></span>
              <span>账面 <b>{{ entry.expected_count }}</b></span>
              <span v-if="entry.missing_codes.length" class="neg">未找到 {{ entry.missing_codes.length }} 个</span>
              <span v-if="entry.extra_codes.length" class="pos">盘盈 {{ entry.extra_codes.length }} 个</span>
            </div>
            <div v-if="entry.checks.some(check => check.scanned)" class="code-list">
              <span v-for="check in entry.checks.filter(item => item.scanned)" :key="check.id" :class="check.expected ? 'expected' : 'extra'">
                {{ check.item_code }}
                <button v-if="current.status === 'in_progress'" title="撤销扫码" @click="undoScan(entry, check)">×</button>
              </span>
            </div>
            <details v-if="entry.missing_codes.length" class="missing-list">
              <summary>查看未扫描编号</summary>
              <span v-for="code in entry.missing_codes" :key="code">{{ code }}</span>
            </details>
          </div>
        </article>
        <div v-if="filteredEntries.length === 0" class="empty">当前筛选条件下没有盘点项。</div>
      </div>
    </div>

    <div v-if="loading" class="loading">处理中…</div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { stocktakeApi } from '../api/stocktake.js'
import { fetchMaterials } from '../api/materials.js'
import { fetchAllLocations, fetchWarehouses } from '../api/warehouses.js'
import { toast } from '../utils/toast.js'
import { filterStocktakeEntries, isNonNegativeInteger, stocktakeProgress } from '../utils/stocktake.js'

defineEmits(['back'])

const list = ref([])
const current = ref(null)
const creating = ref(false)
const newNote = ref('')
const loading = ref(false)
const showSurplus = ref(false)
const filter = ref('all')
const materials = ref([])
const warehouses = ref([])
const locations = ref([])
const scanInputs = reactive({})
const surplus = reactive({ material_id: null, warehouse_id: null, location_id: null, actual_quantity: 0 })
const filters = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待清点' },
  { value: 'discrepancy', label: '有差异' },
]

const filteredEntries = computed(() => {
  if (!current.value) return []
  return filterStocktakeEntries(current.value.entries, filter.value)
})
const progressPercent = computed(() => stocktakeProgress(current.value?.counted_count || 0, current.value?.entries_count || 0))
const surplusLocations = computed(() => locations.value.filter(location => location.warehouse_id === surplus.warehouse_id))

function statusLabel(status) {
  return { in_progress: '进行中', completed: '已完成', cancelled: '已取消' }[status] || status
}
function formatTime(value) { return value ? value.slice(0, 16).replace('T', ' ') : '—' }
function signed(value) { return value > 0 ? `+${value}` : String(value) }
function openCreate() { creating.value = true }

async function withLoading(action) {
  loading.value = true
  try { return await action() } finally { loading.value = false }
}

async function refresh() {
  const response = await withLoading(() => stocktakeApi.list())
  if (response.ok) list.value = response.data
  else toast(response.msg || '盘点记录加载失败', 'error')
}

async function loadMetadata() {
  const [materialResponse, warehouseResponse, locationResponse] = await Promise.all([
    fetchMaterials(), fetchWarehouses(), fetchAllLocations(),
  ])
  if (materialResponse.ok) materials.value = materialResponse.data
  if (warehouseResponse.ok) warehouses.value = warehouseResponse.data
  if (locationResponse.ok) locations.value = locationResponse.data
}

async function doCreate() {
  const response = await withLoading(() => stocktakeApi.create(newNote.value))
  if (!response.ok) return toast(response.msg || '盘点单创建失败', 'error')
  creating.value = false
  newNote.value = ''
  toast(response.msg, 'success')
  await openDetail(response.data.id)
}

async function openDetail(id) {
  const response = await withLoading(() => stocktakeApi.detail(id))
  if (response.ok) current.value = response.data
  else toast(response.msg || '盘点详情加载失败', 'error')
}

async function closeDetail() {
  current.value = null
  showSurplus.value = false
  await refresh()
}

async function updateBulkEntry(entry, event) {
  const raw = String(event.target.value).trim()
  if (!isNonNegativeInteger(raw)) {
    event.target.value = entry.actual_quantity ?? ''
    return toast('请输入非负整数', 'error')
  }
  const response = await withLoading(() => stocktakeApi.updateEntry(current.value.id, entry.id, { actual_quantity: Number(raw) }))
  if (!response.ok) {
    event.target.value = entry.actual_quantity ?? ''
    return toast(response.msg || '数量更新失败', 'error')
  }
  toast(response.msg, 'success')
  await openDetail(current.value.id)
}

async function scanItem(entry) {
  const payload = scanInputs[entry.id]?.trim()
  if (!payload) return
  const response = await withLoading(() => stocktakeApi.scanItem(current.value.id, entry.id, payload))
  if (!response.ok) return toast(response.msg || '扫码失败', 'error')
  scanInputs[entry.id] = ''
  toast(response.msg, 'success')
  await openDetail(current.value.id)
}

async function undoScan(entry, check) {
  const response = await withLoading(() => stocktakeApi.undoScan(current.value.id, entry.id, check.id))
  if (!response.ok) return toast(response.msg || '撤销失败', 'error')
  toast(response.msg, 'success')
  await openDetail(current.value.id)
}

async function confirmIndividual(entry) {
  const response = await withLoading(() => stocktakeApi.confirmEntry(current.value.id, entry.id))
  if (!response.ok) return toast(response.msg || '确认失败', 'error')
  toast(response.msg, entry.missing_codes.length ? 'warning' : 'success')
  await openDetail(current.value.id)
}

async function addSurplus() {
  if (!surplus.material_id || !surplus.warehouse_id) return toast('请选择物资和仓库', 'error')
  const body = { ...surplus, location_id: surplus.location_id || null, actual_quantity: Number(surplus.actual_quantity) }
  const response = await withLoading(() => stocktakeApi.addSurplusEntry(current.value.id, body))
  if (!response.ok) return toast(response.msg || '盘盈项添加失败', 'error')
  Object.assign(surplus, { material_id: null, warehouse_id: null, location_id: null, actual_quantity: 0 })
  showSurplus.value = false
  toast(response.msg, 'success')
  await openDetail(current.value.id)
}

async function doComplete(applyFix) {
  const message = applyFix ? '将按实盘结果修正库存，确定继续？' : '确定完成盘点且不修改库存？'
  if (!window.confirm(message)) return
  const response = await withLoading(() => stocktakeApi.complete(current.value.id, applyFix))
  if (!response.ok) return toast(response.msg || '完成盘点失败', 'error')
  toast(response.msg, 'success')
  await openDetail(current.value.id)
}

async function doCancel() {
  if (!window.confirm('取消后不能继续录入，确定取消这张盘点单？')) return
  const response = await withLoading(() => stocktakeApi.cancel(current.value.id))
  if (!response.ok) return toast(response.msg || '取消失败', 'error')
  toast(response.msg, 'success')
  await closeDetail()
}

onMounted(() => Promise.all([refresh(), loadMetadata()]))
</script>

<style scoped>
.stocktake-page { padding: 20px 28px; color: #1a2332; }
.page-head, .detail-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.title-block { flex: 1; }
.title-block h2, .title-block h3 { margin: 0; }
.title-block small { color: #64748b; }
.detail-actions, .actions-right, .toolbar, .filters, .scan-row, .scan-summary { display: flex; align-items: center; gap: 10px; }
button { font: inherit; }
.btn-back, .btn-ghost, .btn-danger-soft { border: 1.5px solid #dde4ed; border-radius: 10px; padding: 8px 14px; cursor: pointer; background: #fff; color: #475569; }
.btn-primary, .btn-success { color: #fff; border: 0; border-radius: 10px; padding: 10px 18px; cursor: pointer; font-weight: 700; }
.btn-primary { background: linear-gradient(135deg, #667eea, #4facfe); }
.btn-success { background: linear-gradient(135deg, #22c55e, #16a34a); }
.btn-danger-soft { color: #b91c1c; border-color: #fecaca; background: #fff7f7; }
button:disabled { opacity: .45; cursor: not-allowed; }
.panel, .st-card, .progress-card, .detail-summary, .entry-card { background: rgba(255,255,255,.9); border: 1px solid #e8edf3; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,.04); }
.empty { padding: 40px; text-align: center; color: #94a3b8; border: 1.5px dashed #dde4ed; border-radius: 16px; }
.st-card { width: 100%; display: block; text-align: left; padding: 16px 20px; margin-bottom: 12px; cursor: pointer; }
.st-card:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(102,126,234,.13); }
.st-card-top { display: flex; justify-content: space-between; align-items: center; }
.st-id { font-weight: 800; }
.st-status, .count-badge { font-size: 12px; padding: 4px 10px; border-radius: 999px; }
.st-status.in_progress, .count-badge.pending { background: #fef3c7; color: #b45309; }
.st-status.completed, .count-badge.done { background: #dcfce7; color: #15803d; }
.st-status.cancelled { background: #f1f5f9; color: #64748b; }
.st-card-meta, .st-card-stats { display: flex; gap: 18px; margin-top: 9px; color: #64748b; font-size: 13px; }
.st-create { max-width: 560px; padding: 24px; }
.st-create textarea { box-sizing: border-box; width: 100%; min-height: 90px; padding: 12px; border: 1.5px solid #dde4ed; border-radius: 10px; resize: vertical; }
.actions-right { justify-content: flex-end; margin-top: 16px; }
.hint, .muted { color: #64748b; }
.progress-card { padding: 16px 20px; margin-bottom: 14px; }
.progress-copy { display: flex; justify-content: space-between; gap: 16px; font-size: 14px; }
.progress-track { height: 8px; margin-top: 10px; border-radius: 999px; background: #e8edf5; overflow: hidden; }
.progress-track i { display: block; height: 100%; background: linear-gradient(90deg, #667eea, #22c55e); transition: width .25s; }
.detail-summary { display: flex; gap: 36px; padding: 14px 20px; margin-bottom: 14px; }
.toolbar { justify-content: space-between; margin-bottom: 12px; }
.filters button { border: 0; border-radius: 999px; padding: 7px 13px; background: #eef2f7; color: #64748b; cursor: pointer; }
.filters button.active { background: #667eea; color: #fff; }
.surplus-form { display: grid; grid-template-columns: 1.4fr 1fr 1fr .8fr auto; gap: 10px; padding: 14px; margin-bottom: 12px; }
.surplus-form select, .surplus-form input, .bulk-editor input, .scan-row input { border: 1.5px solid #dbe3ec; border-radius: 9px; padding: 9px 11px; background: #fff; }
.entry-card { margin-bottom: 12px; overflow: hidden; }
.entry-card.counted { border-left: 4px solid #22c55e; }
.entry-card.discrepancy { border-left-color: #f59e0b; }
.entry-main { display: grid; grid-template-columns: minmax(180px, 2fr) minmax(140px, 1.2fr) repeat(3, .65fr) auto; gap: 14px; align-items: center; padding: 15px 18px; }
.entry-name small, .entry-location small, .metric small { display: block; margin-top: 3px; color: #94a3b8; }
.metric { text-align: center; }
.bulk-editor, .individual-editor { border-top: 1px solid #eef2f6; padding: 13px 18px; background: #fbfcfe; }
.bulk-editor { display: flex; align-items: center; gap: 10px; color: #64748b; font-size: 13px; }
.bulk-editor input { width: 150px; }
.scan-row input { flex: 1; min-width: 180px; }
.scan-summary { margin-top: 10px; color: #64748b; font-size: 13px; }
.code-list, .missing-list { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
.code-list > span, .missing-list span { border-radius: 999px; padding: 5px 9px; font-size: 12px; background: #e8f7ee; color: #15803d; }
.code-list > span.extra { background: #fff3d6; color: #b45309; }
.code-list button { border: 0; background: transparent; color: inherit; cursor: pointer; font-weight: 900; }
.missing-list { color: #b91c1c; }
.missing-list summary { width: 100%; cursor: pointer; }
.missing-list span { background: #fee2e2; color: #b91c1c; }
.ok, .pos { color: #15803d; }
.warn { color: #b45309; }
.neg { color: #dc2626; }
.loading { position: fixed; right: 24px; bottom: 24px; background: #1e293b; color: #fff; padding: 10px 16px; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,.2); }
@media (max-width: 900px) {
  .detail-head { align-items: flex-start; flex-wrap: wrap; }
  .detail-actions { width: 100%; flex-wrap: wrap; }
  .entry-main { grid-template-columns: 1.5fr 1fr repeat(3, .6fr); }
  .count-badge { grid-column: 1 / -1; justify-self: start; }
  .surplus-form { grid-template-columns: 1fr 1fr; }
  .progress-copy { flex-direction: column; gap: 5px; }
}
</style>
