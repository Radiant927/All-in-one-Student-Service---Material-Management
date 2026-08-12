<template>
  <div class="stocktake-page">
    <div class="page-head">
      <button class="btn-back" @click="$emit('back')">← 返回</button>
      <h2>📋 库存盘点</h2>
      <div class="head-actions">
        <button class="btn-primary" @click="openCreate">＋ 发起盘点</button>
      </div>
    </div>

    <!-- 盘点单列表 -->
    <div v-if="!current && !creating" class="st-list">
      <div v-if="list.length === 0" class="empty">
        <p>还没有盘点记录，点击右上角「发起盘点」开始第一次清点。</p>
      </div>
      <div v-for="s in list" :key="s.id" class="st-card" @click="openDetail(s.id)">
        <div class="st-card-top">
          <span class="st-id">盘点单 #{{ s.id }}</span>
          <span class="st-status" :class="s.status">{{ s.status === 'completed' ? '已完成' : '进行中' }}</span>
        </div>
        <div class="st-card-meta">
          <span>📅 {{ s.created_at.slice(0,16).replace('T',' ') }}</span>
          <span v-if="s.note">📝 {{ s.note }}</span>
        </div>
        <div class="st-card-stats">
          <span>共 <b>{{ s.entries_count }}</b> 项</span>
          <span v-if="s.discrepancy_count > 0" class="warn">⚠️ 差异 <b>{{ s.discrepancy_count }}</b> 项</span>
          <span v-else class="ok">✅ 无差异</span>
        </div>
      </div>
    </div>

    <!-- 创建盘点单 -->
    <div v-if="creating" class="st-create">
      <h3>发起盘点</h3>
      <p class="hint">将按当前库存生成一份账面快照，之后逐项清点填写实际数量。</p>
      <textarea v-model="newNote" placeholder="盘点备注（可选），如：月底例行盘点"></textarea>
      <div class="create-actions">
        <button class="btn-ghost" @click="creating = false">取消</button>
        <button class="btn-primary" @click="doCreate" :disabled="loading">确认发起</button>
      </div>
    </div>

    <!-- 盘点详情 -->
    <div v-if="current" class="st-detail">
      <div class="detail-head">
        <button class="btn-back" @click="current = null; refresh()">← 返回列表</button>
        <h3>盘点单 #{{ current.id }}</h3>
        <div class="detail-actions">
          <button v-if="current.status === 'in_progress'" class="btn-primary" @click="doComplete(false)">完成盘点</button>
          <button v-if="current.status === 'in_progress'" class="btn-success" @click="doComplete(true)">完成并修正库存</button>
        </div>
      </div>

      <div class="detail-summary">
        <span>账面总数：<b>{{ current.total_book }}</b></span>
        <span>实际总数：<b>{{ current.total_actual }}</b></span>
        <span :class="current.total_difference === 0 ? 'ok' : 'warn'">
          差异：<b>{{ current.total_difference > 0 ? '+' : '' }}{{ current.total_difference }}</b>
        </span>
      </div>

      <div class="detail-table">
        <div class="dt-row dt-head">
          <span>物资</span><span>仓库</span><span>账面</span><span>实际</span><span>差异</span>
        </div>
        <div v-for="e in current.entries" :key="e.id" class="dt-row">
          <span class="dt-name">{{ e.material_name }}<small>{{ e.material_spec }}</small></span>
          <span>{{ e.warehouse_name }}</span>
          <span class="dt-book">{{ e.book_quantity }}</span>
          <span>
            <input
              v-if="current.status === 'in_progress'"
              type="number" min="0"
              :value="e.actual_quantity === null ? e.book_quantity : e.actual_quantity"
              @change="updateEntry(e, $event)"
              class="qty-input"
            />
            <span v-else>{{ e.actual_quantity }}</span>
          </span>
          <span :class="e.difference === 0 ? 'ok' : (e.difference > 0 ? 'pos' : 'neg')">
            {{ e.difference > 0 ? '+' : '' }}{{ e.difference }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中…</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { stocktakeApi } from '../api/stocktake.js'

const emit = defineEmits(['back'])

const list = ref([])
const current = ref(null)
const creating = ref(false)
const newNote = ref('')
const loading = ref(false)

async function refresh() {
  loading.value = true
  const res = await stocktakeApi.list()
  if (res.ok) list.value = res.data
  loading.value = false
}

function openCreate() { creating.value = true }

async function doCreate() {
  const res = await stocktakeApi.create(newNote.value)
  if (res.ok) {
    creating.value = false
    newNote.value = ''
    await refresh()
    await openDetail(res.data.id)
  }
}

async function openDetail(id) {
  loading.value = true
  const res = await stocktakeApi.detail(id)
  if (res.ok) current.value = res.data
  loading.value = false
}

async function updateEntry(e, ev) {
  const raw = String(ev.target.value).trim()
  if (raw === '') return
  // 只允许非负整数，拒绝小数/负数/非法输入
  if (!/^\d+$/.test(raw)) {
    ev.target.value = e.actual_quantity ?? e.book_quantity
    alert('请输入非负整数')
    return
  }
  const val = parseInt(raw, 10)
  const res = await stocktakeApi.updateEntry(current.value.id, e.id, {
    material_id: e.material_id,
    warehouse_id: e.warehouse_id,
    location_id: e.location_id,
    actual_quantity: val,
  })
  if (res.ok) {
    e.actual_quantity = res.data.actual_quantity
    e.difference = res.data.difference
    current.value.total_actual = current.value.entries.reduce((s, x) => s + (x.actual_quantity || 0), 0)
    current.value.total_difference = current.value.entries.reduce((s, x) => s + x.difference, 0)
  } else {
    alert(res.msg || '更新失败')
    ev.target.value = e.actual_quantity ?? e.book_quantity
  }
}

async function doComplete(applyFix) {
  if (!confirm(applyFix ? '将把系统库存修正为实际清点数量，确定完成？' : '确定完成盘点？（不会修改库存）')) return
  const res = await stocktakeApi.complete(current.value.id, applyFix)
  if (res.ok) {
    alert(res.msg || '盘点完成')
    await openDetail(current.value.id)
    await refresh()
  } else {
    alert(res.msg || '操作失败')
  }
}

onMounted(refresh)
</script>

<style scoped>
.stocktake-page { padding: 20px 28px; }
.page-head, .detail-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-head h2, .detail-head h3 { flex: 1; margin: 0; color: #1a2332; }
.head-actions, .detail-actions { display: flex; gap: 10px; }
.btn-back { background: none; border: 1.5px solid #dde4ed; border-radius: 10px; padding: 8px 14px; cursor: pointer; color: #5a6b7d; }
.btn-back:hover { border-color: #667eea; color: #667eea; }
.btn-primary { background: linear-gradient(135deg,#667eea,#4facfe); color: #fff; border: none; border-radius: 10px; padding: 10px 18px; cursor: pointer; font-weight: 600; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-success { background: linear-gradient(135deg,#22c55e,#16a34a); color: #fff; border: none; border-radius: 10px; padding: 10px 18px; cursor: pointer; font-weight: 600; }
.btn-ghost { background: #f1f5f9; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 10px 18px; cursor: pointer; color: #475569; }

.empty { background: rgba(255,255,255,0.7); border: 1.5px dashed #dde4ed; border-radius: 16px; padding: 40px; text-align: center; color: #94a3b8; }
.st-card { background: rgba(255,255,255,0.85); border: 1px solid rgba(255,255,255,0.6); border-radius: 16px; padding: 16px 20px; margin-bottom: 12px; cursor: pointer; box-shadow: 0 2px 12px rgba(0,0,0,0.05); transition: 0.2s; }
.st-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102,126,234,0.15); }
.st-card-top { display: flex; justify-content: space-between; align-items: center; }
.st-id { font-weight: 700; color: #1a2332; }
.st-status { font-size: 12px; padding: 3px 10px; border-radius: 20px; }
.st-status.in_progress { background: #fef3c7; color: #b45309; }
.st-status.completed { background: #dcfce7; color: #15803d; }
.st-card-meta { color: #64748b; font-size: 13px; margin: 8px 0; display: flex; gap: 16px; }
.st-card-stats { display: flex; gap: 16px; font-size: 14px; }
.warn { color: #d97706; }
.ok { color: #16a34a; }
.pos { color: #16a34a; font-weight: 700; }
.neg { color: #dc2626; font-weight: 700; }

.st-create { background: rgba(255,255,255,0.9); border-radius: 16px; padding: 24px; max-width: 520px; }
.st-create h3 { margin: 0 0 8px; }
.hint { color: #64748b; font-size: 14px; margin-bottom: 16px; }
.st-create textarea { width: 100%; min-height: 80px; border: 1.5px solid #dde4ed; border-radius: 10px; padding: 12px; font-family: inherit; resize: vertical; }
.create-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }

.detail-summary { display: flex; gap: 30px; background: rgba(255,255,255,0.85); border-radius: 14px; padding: 14px 20px; margin-bottom: 16px; font-size: 15px; }
.detail-table { background: rgba(255,255,255,0.9); border-radius: 14px; overflow: hidden; }
.dt-row { display: grid; grid-template-columns: 2fr 1.2fr 0.8fr 0.9fr 0.8fr; padding: 12px 16px; border-bottom: 1px solid #f1f5f9; align-items: center; }
.dt-head { background: #f8fafc; font-weight: 700; color: #475569; font-size: 13px; }
.dt-name { font-weight: 600; color: #1a2332; }
.dt-name small { display: block; font-weight: 400; color: #94a3b8; font-size: 12px; }
.qty-input { width: 70px; border: 1.5px solid #dde4ed; border-radius: 8px; padding: 6px 8px; text-align: center; }
.loading { text-align: center; color: #94a3b8; padding: 30px; }
</style>
