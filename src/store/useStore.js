import { reactive, computed } from 'vue'
import { fetchMaterials, fetchMaterial, createMaterial, updateMaterial, deleteMaterial } from '../api/materials.js'
import { fetchWarehouses, fetchAllLocations, fetchWarehouseStats, fetchWarehouseDetail, fetchMaterialWarehouseBreakdown } from '../api/warehouses.js'
import { fetchInventoryItems, addInventoryItems, deleteInventoryItem, updateInventoryBatch, inbound as apiInbound } from '../api/inventory.js'
import { borrow as apiBorrow, returnItem as apiReturn, fetchHistory } from '../api/borrow.js'
import { verifyPassword as apiVerifyPassword } from '../api/admin.js'
import { transfer as apiTransfer } from '../api/transfer.js'
import { fetchDashboardAlerts, fetchRestockSuggestions, sendReportEmail } from '../api/reports.js'

const state = reactive({
  materials: [],
  warehouses: [],
  locations: [],
  warehouseStats: [],
  borrowHistory: [],
  adminLoggedIn: false,
  loading: false,
  currentView: 'all',
  dashboardAlerts: null,
  restockReport: null,
})

// --- Loaders ---
async function loadMaterials() {
  state.loading = true
  const res = await fetchMaterials()
  if (res.ok) {
    state.materials = res.data.map(m => ({
      ...m,
      type: m.category,
      totalQuantity: m.total_quantity,
      borrowedQuantity: m.borrowed_quantity,
      items: null,
    }))
  }
  state.loading = false
}

async function loadWarehouses() {
  const [whRes, locRes] = await Promise.all([fetchWarehouses(), fetchAllLocations()])
  if (whRes.ok) state.warehouses = whRes.data
  if (locRes.ok) state.locations = locRes.data
}

async function loadHistory() {
  const res = await fetchHistory({ limit: 50 })
  if (res.ok) state.borrowHistory = res.data.rows || []
}

async function loadAll() {
  await Promise.all([loadMaterials(), loadWarehouses(), loadHistory(), loadDashboardAlerts()])
}

async function loadDashboardAlerts() {
  const res = await fetchDashboardAlerts(30)
  if (res.ok) state.dashboardAlerts = res.data
  return res
}

async function loadRestockReport(windowDays = 30) {
  const res = await fetchRestockSuggestions(windowDays)
  if (res.ok) state.restockReport = res.data
  return res
}

async function loadWarehouseStats() {
  const res = await fetchWarehouseStats()
  if (res.ok) state.warehouseStats = res.data
  return res
}

async function loadWarehouseDetail(id) {
  const res = await fetchWarehouseDetail(id)
  return res
}

async function loadMaterialWarehouseBreakdown(materialId) {
  const res = await fetchMaterialWarehouseBreakdown(materialId)
  return res.ok ? res.data : []
}

// --- Getters ---
const allMaterials = computed(() => state.materials)

const durableMaterials = computed(() =>
  allMaterials.value.filter(m => m.type === 'durable')
)

const consumableMaterials = computed(() =>
  allMaterials.value.filter(m => m.type === 'consumable')
)

const totalTypes = computed(() => allMaterials.value.length)

const durableCount = computed(() =>
  durableMaterials.value.reduce((s, m) => s + (m.totalQuantity || 0), 0)
)

const consumableCount = computed(() =>
  consumableMaterials.value.reduce((s, m) => s + (m.totalQuantity || 0), 0)
)

const availableCount = computed(() =>
  allMaterials.value.reduce((s, m) => s + getRemaining(m), 0)
)

const recentHistory = computed(() =>
  [...state.borrowHistory].reverse().slice(0, 20)
)

const alertCount = computed(() =>
  (state.dashboardAlerts?.critical_count || 0) + (state.dashboardAlerts?.warning_count || 0)
)

const criticalAlerts = computed(() =>
  state.dashboardAlerts?.top_alerts?.filter(a => a.status === 'critical') || []
)

const allAlerts = computed(() =>
  state.dashboardAlerts?.top_alerts || []
)

// --- Helpers ---
function getRemaining(m) {
  if (m.has_individual_tracking && m.items) {
    return m.items.filter(i => i.status === 'available').length
  }
  return m.available_quantity ?? Math.max(0, (m.totalQuantity || 0) - (m.borrowedQuantity || 0))
}

function getMaterial(id) {
  return allMaterials.value.find(m => m.id === id)
}

async function getAvailableItems(materialId) {
  const res = await fetchInventoryItems(materialId, { status: 'available' })
  return res.ok ? res.data : []
}

async function getBorrowedItems(materialId) {
  const res = await fetchInventoryItems(materialId, { status: 'borrowed' })
  return res.ok ? res.data : []
}

async function loadItemsForMaterial(materialId) {
  const m = getMaterial(materialId)
  if (!m || !m.has_individual_tracking) return
  const res = await fetchInventoryItems(materialId)
  if (res.ok) {
    m.items = res.data.map(item => ({
      code: item.code,
      status: item.status,
      borrowedBy: item.borrowed_by,
      borrowTime: item.borrow_time,
    }))
    m.totalQuantity = m.items.length
    m.borrowedQuantity = m.items.filter(i => i.status === 'borrowed').length
    m.available_quantity = m.items.filter(i => i.status === 'available').length
  }
}

// --- Actions ---
async function borrowItemFn(materialId, quantity, borrower) {
  const res = await apiBorrow({ material_id: materialId, quantity, borrower })
  if (res.ok) await loadAll()
  return res
}

async function borrowIndividualItemFn(materialId, itemCode, borrower) {
  const res = await apiBorrow({ material_id: materialId, quantity: 1, borrower, item_code: itemCode })
  if (res.ok) await loadAll()
  return res
}

async function returnItemFn(materialId, quantity, returnedBy) {
  const res = await apiReturn({ material_id: materialId, quantity, returned_by: returnedBy })
  if (res.ok) await loadAll()
  return res
}

async function returnIndividualItemFn(materialId, itemCode, returnedBy) {
  const res = await apiReturn({ material_id: materialId, quantity: 1, returned_by: returnedBy, item_code: itemCode })
  if (res.ok) await loadAll()
  return res
}

async function updateTotalQuantityFn(materialId, newTotal) {
  const m = getMaterial(materialId)
  if (!m) return { ok: false, msg: '物资不存在' }
  const val = parseInt(newTotal, 10)
  if (isNaN(val) || val < 0) return { ok: false, msg: '请输入有效数量' }
  if (val < (m.borrowedQuantity || 0)) return { ok: false, msg: '总数不能小于已借出数量' }
  const res = await updateInventoryBatch(materialId, { quantity: val })
  if (res.ok) await loadAll()
  return res
}

async function updateThresholdFn(materialId, newThreshold) {
  const val = parseInt(newThreshold, 10)
  if (isNaN(val) || val < 0) return { ok: false, msg: '请输入有效阈值' }
  const res = await updateMaterial(materialId, { low_stock_threshold: val })
  if (res.ok) await loadAll()
  return res
}

async function addRemoteItemsFn(materialId, prefix, startNum, count) {
  const m = getMaterial(materialId)
  if (!m) return { ok: false, msg: '物资不存在' }
  const warehouseId = state.warehouses[0]?.id || 1
  const res = await addInventoryItems({
    material_id: materialId,
    warehouse_id: warehouseId,
    prefix,
    start_num: startNum,
    count,
  })
  if (res.ok) await loadAll()
  return res
}

async function removeRemoteItemFn(materialId, itemCode) {
  const m = getMaterial(materialId)
  if (!m) return { ok: false, msg: '物资不存在' }
  if (!m.items) {
    await loadItemsForMaterial(materialId)
  }
  const item = m.items?.find(i => i.code === itemCode)
  if (!item) return { ok: false, msg: `遥控器 ${itemCode} 不存在` }
  if (item.status === 'borrowed') return { ok: false, msg: `遥控器 ${itemCode} 已被借出，请先归还再删除` }

  const fullItem = (await fetchInventoryItems(materialId, { search: itemCode })).data?.[0]
  if (!fullItem) return { ok: false, msg: `遥控器 ${itemCode} 不存在` }
  const res = await deleteInventoryItem(fullItem.id)
  if (res.ok) await loadAll()
  return res
}

async function verifyPasswordFn(password) {
  const res = await apiVerifyPassword(password)
  return res
}

async function createMaterialFn(data) {
  const res = await createMaterial(data)
  if (res.ok) await loadAll()
  return res
}

async function updateMaterialFn(id, data) {
  const res = await updateMaterial(id, data)
  if (res.ok) await loadAll()
  return res
}

async function deleteMaterialFn(id) {
  const res = await deleteMaterial(id)
  if (res.ok) await loadAll()
  return res
}

async function transferFn(data) {
  const res = await apiTransfer(data)
  if (res.ok) await loadAll()
  return res
}

async function inboundFn(data) {
  const res = await apiInbound(data)
  if (res.ok) await loadAll()
  return res
}

async function sendReportEmailFn() {
  const res = await sendReportEmail()
  return res
}

export function useStore() {
  return {
    state,
    allMaterials,
    durableMaterials,
    consumableMaterials,
    totalTypes,
    durableCount,
    consumableCount,
    availableCount,
    recentHistory,
    getRemaining,
    getMaterial,
    getAvailableItems,
    getBorrowedItems,
    loadAll,
    loadMaterials,
    loadWarehouses,
    loadHistory,
    loadItemsForMaterial,
    loadWarehouseStats,
    loadWarehouseDetail,
    loadMaterialWarehouseBreakdown,
    borrowItem: borrowItemFn,
    borrowIndividualItem: borrowIndividualItemFn,
    returnItem: returnItemFn,
    returnIndividualItem: returnIndividualItemFn,
    updateTotalQuantity: updateTotalQuantityFn,
    updateThreshold: updateThresholdFn,
    addRemoteItems: addRemoteItemsFn,
    removeRemoteItem: removeRemoteItemFn,
    verifyPassword: verifyPasswordFn,
    createMaterial: createMaterialFn,
    updateMaterial: updateMaterialFn,
    deleteMaterial: deleteMaterialFn,
    transfer: transferFn,
    inbound: inboundFn,
    dashboardAlerts: computed(() => state.dashboardAlerts),
    alertCount,
    criticalAlerts,
    allAlerts,
    loadDashboardAlerts,
    loadRestockReport,
    sendReportEmail: sendReportEmailFn,
  }
}