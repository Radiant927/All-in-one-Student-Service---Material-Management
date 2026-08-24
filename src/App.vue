<template>
  <div class="bg-decoration">
    <div class="bg-blob"></div>
    <div class="bg-blob"></div>
    <div class="bg-blob"></div>
  </div>

  <ToastContainer ref="toastRef" />

  <div id="app">
    <AppHeader
        :alert-badge="alertCount"
        @toggle-admin="showAdminPanel = true"
        @toggle-archive="showArchiveForm = true"
        @toggle-import="showImportModal = true"
        @toggle-warehouse="toggleView"
        @toggle-reports="toggleReports"
@toggle-stocktake="toggleStocktake"
        @toggle-applications="toggleApplications"
      />

    <AlertBanner
      v-if="currentView === 'all' && allAlerts.length > 0"
      :alerts="allAlerts"
      :critical-count="dashboardAlerts?.critical_count || 0"
      :warning-count="dashboardAlerts?.warning_count || 0"
      @view-reports="currentView = 'reports'"
    />

    <StatsRow
      v-if="currentView === 'all'"
      :total-types="totalTypes"
      :durable-count="durableCount"
      :consumable-count="consumableCount"
      :available-count="availableCount"
      :alert-count="alertCount"
    />

    <!-- Warehouse View -->
    <WarehousePage
      v-if="currentView === 'warehouse'"
      @view-detail="openWarehouseDetail"
      @view-all="currentView = 'all'"
    />

    <!-- Warehouse Detail -->
    <WarehouseDetail
      v-if="currentView === 'detail'"
      :warehouse-id="detailWarehouseId"
      @back="currentView = 'warehouse'"
      @inbound="openInboundModal"
      @transfer="openTransferModal"
    />

    <!-- Reports Page -->
    <ReportsPage
      v-if="currentView === 'reports'"
      :toast="toast"
      @back="currentView = 'all'"
    />

<!-- Stocktake Page -->
    <StocktakePage
      v-if="currentView === 'stocktake'"
      @back="currentView = 'all'"
    />

    <BorrowApplicationsPage
      v-if="currentView === 'applications'"
      :toast="toast"
      @back="currentView = 'all'"
    />

    <div v-if="currentView === 'all'" class="card-grid">
      <template v-if="durableMaterials.length > 0">
        <div class="category-section">
          <div class="category-header">
            <span class="cat-icon cat-durable">🔧</span>
            <span>固定性物资</span>
            <span class="cat-count">共 {{ durableMaterials.length }} 种 · {{ durableCount }} 件</span>
          </div>
        </div>
        <MaterialCard
          v-for="m in durableMaterials"
          :key="m.id"
          :material="m"
          :remaining="getRemaining(m)"
          :borrowed="m.borrowedQuantity || 0"
          :total="m.items ? m.items.length : m.totalQuantity"
          @borrow="openBorrowModal"
          @return="openReturnModal"
          @manage="openManagementPage"
        />
      </template>

      <template v-if="consumableMaterials.length > 0">
        <div class="category-section">
          <div class="category-header">
            <span class="cat-icon cat-consumable">📦</span>
            <span>消耗性物资</span>
            <span class="cat-count">共 {{ consumableMaterials.length }} 种 · {{ consumableCount }} 件</span>
          </div>
        </div>
        <MaterialCard
          v-for="m in consumableMaterials"
          :key="m.id"
          :material="m"
          :remaining="getRemaining(m)"
          :borrowed="m.borrowedQuantity || 0"
          :total="m.totalQuantity || 0"
          @borrow="openBorrowModal"
          @return="openReturnModal"
        />
      </template>
    </div>

    <HistorySection v-if="currentView === 'all'" :history="recentHistory" :materials="allMaterials" />
    <footer class="footer">© 2026 一站式物资管理系统 · 数据已持久化存储</footer>
  </div>

  <BorrowModal
    :visible="borrowModalVisible"
    :material="borrowMaterial"
    :remaining="borrowRemaining"
    :available-items="borrowAvailableItems"
    @close="borrowModalVisible = false"
    @confirm="handleBorrow"
  />

  <ReturnModal
    :visible="returnModalVisible"
    :material="returnMaterial"
    :borrowed-items="returnBorrowedItems"
    @close="returnModalVisible = false"
    @confirm="handleReturn"
  />

  <ManagementPage
    :visible="managementVisible"
    :material="managementMaterial"
    @close="managementVisible = false"
    @show-qr="openQRModal"
    @borrow-item="openItemBorrowModal"
    @return-item="openItemReturnModal"
    @delete-item="handleDeleteItem"
    @add-remote="showAddRemoteModal = true"
    @print-all-qr="printAllQR"
  />

  <QRModal
    :visible="qrModalVisible"
    :item-code="qrItemCode"
    @close="qrModalVisible = false"
    @print-qr="printQR"
  />

  <AddRemoteModal
    :visible="showAddRemoteModal"
    :next-start-num="nextRemoteNum"
    @close="showAddRemoteModal = false"
    @confirm="handleAddRemotes"
  />

  <ItemBorrowModal
    :visible="itemBorrowModalVisible"
    :item-code="itemBorrowCode"
    @close="itemBorrowModalVisible = false"
    @confirm="handleItemBorrow"
  />

  <ItemReturnModal
    :visible="itemReturnModalVisible"
    :item-code="itemReturnCode"
    :current-borrower="itemReturnCurrentBorrower"
    @close="itemReturnModalVisible = false"
    @confirm="handleItemReturn"
  />

  <AdminPanel
    :visible="showAdminPanel"
    :logged-in="adminLoggedIn"
    :materials="allMaterials"
    @close="showAdminPanel = false"
    @login="handleAdminLogin"
    @logout="handleAdminLogout"
    @save-total="handleSaveTotal"
    @save-threshold="handleSaveThreshold"
    @toggle-locations="showLocationManager = true"
    @toggle-import="showImportModal = true"
    @toggle-users="showUserManager = true"
  />

  <MaterialArchiveForm
    :visible="showArchiveForm"
    :material="editingMaterial"
    @close="showArchiveForm = false; editingMaterial = null"
    @submit="handleArchiveSubmit"
  />

  <ImportExcelModal
    :visible="showImportModal"
    @close="showImportModal = false"
    @imported="handleImported"
  />

  <LocationManager
    :visible="showLocationManager"
    @close="showLocationManager = false"
  />

  <UserManager
    :visible="showUserManager"
    :toast="toast"
    @close="showUserManager = false"
  />

  <InboundModal
    :visible="inboundModalVisible"
    :preselected-warehouse-id="inboundWarehouseId"
    @close="inboundModalVisible = false"
    @done="handleInboundDone"
  />

  <TransferModal
    :visible="transferModalVisible"
    :preselected-warehouse-id="transferWarehouseId"
    @close="transferModalVisible = false"
    @done="handleTransferDone"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from './store/useStore.js'
import AppHeader from './components/AppHeader.vue'
import StatsRow from './components/StatsRow.vue'
import MaterialCard from './components/MaterialCard.vue'
import HistorySection from './components/HistorySection.vue'
import BorrowModal from './components/BorrowModal.vue'
import ReturnModal from './components/ReturnModal.vue'
import ManagementPage from './components/ManagementPage.vue'
import QRModal from './components/QRModal.vue'
import AddRemoteModal from './components/AddRemoteModal.vue'
import ItemBorrowModal from './components/ItemBorrowModal.vue'
import ItemReturnModal from './components/ItemReturnModal.vue'
import AdminPanel from './components/AdminPanel.vue'
import MaterialArchiveForm from './components/MaterialArchiveForm.vue'
import ImportExcelModal from './components/ImportExcelModal.vue'
import LocationManager from './components/LocationManager.vue'
import UserManager from './components/UserManager.vue'
import WarehousePage from './components/WarehousePage.vue'
import WarehouseDetail from './components/WarehouseDetail.vue'
import InboundModal from './components/InboundModal.vue'
import TransferModal from './components/TransferModal.vue'
import AlertBanner from './components/AlertBanner.vue'
import ReportsPage from './components/ReportsPage.vue'
import StocktakePage from './components/StocktakePage.vue'
import BorrowApplicationsPage from './components/BorrowApplicationsPage.vue'
import ToastContainer from './components/ToastContainer.vue'
import QRCode from 'qrcode'
import { clearAuthTokens } from './api/client.js'

const {
  allMaterials, durableMaterials, consumableMaterials,
  totalTypes, durableCount, consumableCount, availableCount, recentHistory,
  getRemaining, getMaterial, getAvailableItems, getBorrowedItems,
  borrowItem, borrowIndividualItem, returnItem, returnIndividualItem,
  updateTotalQuantity, updateThreshold, addRemoteItems, removeRemoteItem,
  verifyPassword, loadAll, loadItemsForMaterial, createMaterial, updateMaterial,
  loadWarehouseStats, transfer, inbound,
  alertCount, allAlerts, dashboardAlerts, sendReportEmail
} = useStore()

const toastRef = ref(null)
function toast(msg, type = 'info') { toastRef.value?.show(msg, type) }

const remoteMaterial = computed(() =>
  durableMaterials.value.find(m => m.has_individual_tracking)
)
const remoteMaterialId = computed(() => remoteMaterial.value?.id)

onMounted(() => {
  loadAll()
})

// Borrow modal
const borrowModalVisible = ref(false)
const borrowMaterial = ref(null)
const borrowRemaining = ref(0)
const borrowAvailableItems = ref([])

async function openBorrowModal(materialId) {
  const m = getMaterial(materialId)
  if (!m) return
  borrowMaterial.value = m
  borrowRemaining.value = getRemaining(m)
  borrowAvailableItems.value = await getAvailableItems(materialId)
  borrowModalVisible.value = true
}

async function handleBorrow({ materialId, borrower, itemCode, quantity }) {
  const m = getMaterial(materialId)
  if (!m) return
  if (m.has_individual_tracking) {
    if (!itemCode) { toast('没有可用的遥控器', 'error'); return }
    const result = await borrowIndividualItem(materialId, itemCode, borrower)
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) borrowModalVisible.value = false
  } else {
    if (!borrower?.trim()) { toast('请输入借用人姓名', 'error'); return }
    const result = await borrowItem(materialId, quantity, borrower.trim())
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) borrowModalVisible.value = false
  }
}

// Return modal
const returnModalVisible = ref(false)
const returnMaterial = ref(null)
const returnBorrowedItems = ref([])

async function openReturnModal(materialId) {
  const m = getMaterial(materialId)
  if (!m) return
  returnMaterial.value = m
  returnBorrowedItems.value = await getBorrowedItems(materialId)
  returnModalVisible.value = true
}

async function handleReturn({ materialId, returner, itemCode, quantity }) {
  const m = getMaterial(materialId)
  if (!m) return
  if (m.has_individual_tracking) {
    if (!itemCode) { toast('没有已借出的遥控器', 'error'); return }
    const result = await returnIndividualItem(materialId, itemCode, returner)
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) returnModalVisible.value = false
  } else {
    const result = await returnItem(materialId, quantity, returner)
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) returnModalVisible.value = false
  }
}

// Management page
const managementVisible = ref(false)
const managementMaterial = ref(null)

function openManagementPage(materialId) {
  const m = getMaterial(materialId)
  if (!m) return
  managementMaterial.value = m
  managementVisible.value = true
}

// QR modal
const qrModalVisible = ref(false)
const qrItemCode = ref('')

function openQRModal(itemCode) {
  qrItemCode.value = itemCode
  qrModalVisible.value = true
}

function escHtml(s) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }
  return String(s).replace(/[&<>"']/g, c => map[c])
}

function printQR(itemCode) {
  const safeCode = escHtml(itemCode)
  const canvas = document.createElement('canvas')
  QRCode.toCanvas(canvas, `ITEM:${itemCode}`, {
    width: 250,
    color: { dark: '#1a2332', light: '#ffffff' }
  }).then(() => {
    const dataUrl = canvas.toDataURL('image/png')
    const w = window.open('', '_blank', 'width=400,height=500')
    w.document.write(`<!DOCTYPE html><html><head><title>打印二维码 - ${safeCode}</title><style>body{text-align:center;padding:30px;font-family:sans-serif;}img{border:2px dashed #ddd;padding:10px;}</style></head><body><h2>🔑 ${safeCode}</h2><p>空调遥控器 - 专属二维码</p><img src="${dataUrl}" width="250" height="250"><p style="margin-top:16px;font-size:13px;color:#888;">扫描二维码进行借出登记</p></body></html>`)
    w.document.close()
    setTimeout(() => w.print(), 400)
  })
}

function printAllQR() {
  const m = remoteMaterial.value
  if (!m?.items) return
  const safeName = escHtml(m.name)
  const safeIcon = escHtml(m.icon)
  const w = window.open('', '_blank', 'width=900,height=700')
  w.document.write(`<!DOCTYPE html><html><head><title>打印全部二维码</title><style>body{font-family:sans-serif;padding:20px;}h2{text-align:center;}.subtitle{text-align:center;color:#666;font-size:14px;margin-bottom:20px;}.qr-grid{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;}.qr-item{text-align:center;width:180px;padding:12px;border:1px dashed #ddd;border-radius:8px;}.qr-item .code{font-weight:bold;margin-bottom:6px;}@media print{.qr-item{page-break-inside:avoid;}}</style></head><body><h2>${safeIcon} ${safeName} - 二维码清单</h2><p class="subtitle">共 ${m.items.length} 个遥控器</p><div class="qr-grid" id="printQrGrid"></div></body></html>`)
  w.document.close()
  setTimeout(() => {
    const grid = w.document.getElementById('printQrGrid')
    m.items.forEach(i => {
      const div = w.document.createElement('div')
      div.className = 'qr-item'
      const safeCode = escHtml(i.code)
      div.innerHTML = `<div class="code">🔑 ${safeCode}</div>`
      grid.appendChild(div)
      const cv = w.document.createElement('canvas')
      QRCode.toCanvas(cv, `ITEM:${i.code}`, { width: 130, color: { dark: '#1a2332', light: '#ffffff' } }).then(() => div.appendChild(cv))
    })
    setTimeout(() => w.print(), 800)
  }, 300)
}

// Add remote
const showAddRemoteModal = ref(false)
const nextRemoteNum = computed(() => {
  const m = remoteMaterial.value
  if (!m?.items) return 1
  return m.items.reduce((max, i) => {
    const match = i.code.match(/\d+$/)
    return match ? Math.max(max, parseInt(match[0], 10)) : max
  }, 0) + 1
})

async function handleAddRemotes({ prefix, startNum, count }) {
  if (isNaN(startNum) || startNum < 1) { toast('请输入有效的起始编号', 'error'); return }
  if (isNaN(count) || count < 1 || count > 50) { toast('添加数量需在 1~50 之间', 'error'); return }
  if (!remoteMaterialId.value) { toast('未找到遥控器物资', 'error'); return }
  const result = await addRemoteItems(remoteMaterialId.value, prefix, startNum, count)
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) showAddRemoteModal.value = false
}

// Item borrow
const itemBorrowModalVisible = ref(false)
const itemBorrowCode = ref('')

function openItemBorrowModal(itemCode) {
  itemBorrowCode.value = itemCode
  itemBorrowModalVisible.value = true
}

async function handleItemBorrow({ itemCode, borrower }) {
  if (!remoteMaterialId.value) { toast('未找到遥控器物资', 'error'); return }
  const result = await borrowIndividualItem(remoteMaterialId.value, itemCode, borrower)
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) itemBorrowModalVisible.value = false
}

// Item return
const itemReturnModalVisible = ref(false)
const itemReturnCode = ref('')
const itemReturnCurrentBorrower = ref('')

function openItemReturnModal(itemCode) {
  const m = remoteMaterial.value
  const item = m?.items?.find(i => i.code === itemCode)
  if (!item) { toast(`遥控器 ${itemCode} 未被借出`, 'error'); return }
  itemReturnCode.value = itemCode
  itemReturnCurrentBorrower.value = item.borrowed_by || '未知'
  itemReturnModalVisible.value = true
}

async function handleItemReturn({ itemCode, returner }) {
  if (!remoteMaterialId.value) { toast('未找到遥控器物资', 'error'); return }
  const result = await returnIndividualItem(remoteMaterialId.value, itemCode, returner)
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) itemReturnModalVisible.value = false
}

// Delete item
async function handleDeleteItem(itemCode) {
  if (!confirm(`确定要删除遥控器 ${itemCode} 吗？此操作不可恢复。`)) return
  if (!remoteMaterialId.value) { toast('未找到遥控器物资', 'error'); return }
  const result = await removeRemoteItem(remoteMaterialId.value, itemCode)
  toast(result.msg, result.ok ? 'success' : 'error')
}

// Admin
const showAdminPanel = ref(false)
const adminLoggedIn = ref(false)

async function handleAdminLogin(password) {
  const res = await verifyPassword(password)
  if (res.ok) {
    adminLoggedIn.value = true
    toast('管理员验证成功', 'success')
  } else {
    toast('密码错误', 'error')
  }
}

function handleAdminLogout() {
  adminLoggedIn.value = false
  clearAuthTokens()
}

async function handleSaveTotal(materialId, newTotal) {
  const result = await updateTotalQuantity(materialId, newTotal)
  toast(result.msg, result.ok ? 'success' : 'error')
}

async function handleSaveThreshold(materialId, newThreshold) {
  const result = await updateThreshold(materialId, newThreshold)
  toast(result.msg, result.ok ? 'success' : 'error')
}

// Archive form
const showArchiveForm = ref(false)
const editingMaterial = ref(null)

async function handleArchiveSubmit(formData) {
  let result
  if (editingMaterial.value) {
    result = await updateMaterial(editingMaterial.value.id, formData)
  } else {
    result = await createMaterial(formData)
  }
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) {
    showArchiveForm.value = false
    editingMaterial.value = null
  }
}

// Import modal
const showImportModal = ref(false)

function handleImported() {
  loadAll()
  toast('导入成功，数据已刷新', 'success')
}

// Location manager
const showLocationManager = ref(false)
const showUserManager = ref(false)

// Warehouse view
const currentView = ref('all')
const detailWarehouseId = ref(null)
const inboundModalVisible = ref(false)
const inboundWarehouseId = ref(null)
const transferModalVisible = ref(false)
const transferWarehouseId = ref(null)

function toggleView() {
  if (currentView.value === 'all') {
    currentView.value = 'warehouse'
  } else {
    currentView.value = 'all'
  }
}

function toggleReports() {
  currentView.value = currentView.value === 'reports' ? 'all' : 'reports'
}

function toggleStocktake() {
  currentView.value = currentView.value === 'stocktake' ? 'all' : 'stocktake'
}

function toggleApplications() {
  currentView.value = currentView.value === 'applications' ? 'all' : 'applications'
}

function openWarehouseDetail(warehouseId) {
  detailWarehouseId.value = warehouseId
  currentView.value = 'detail'
}

function openInboundModal(warehouseId) {
  inboundWarehouseId.value = warehouseId
  inboundModalVisible.value = true
}

function handleInboundDone(res) {
  inboundModalVisible.value = false
  toast(res.msg || '入库成功', 'success')
  loadAll()
}

function openTransferModal(warehouseId) {
  transferWarehouseId.value = warehouseId
  transferModalVisible.value = true
}

function handleTransferDone(res) {
  transferModalVisible.value = false
  toast(res.msg || '调拨成功', 'success')
  loadAll()
}

// ESC to close modals
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return
  borrowModalVisible.value = false
  returnModalVisible.value = false
  qrModalVisible.value = false
  itemBorrowModalVisible.value = false
  itemReturnModalVisible.value = false
  showAddRemoteModal.value = false
  showAdminPanel.value = false
  managementVisible.value = false
  inboundModalVisible.value = false
  transferModalVisible.value = false
  showImportModal.value = false
  showUserManager.value = false
})
</script>
