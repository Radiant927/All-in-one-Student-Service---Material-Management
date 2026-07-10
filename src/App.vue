<template>
  <div class="bg-decoration">
    <div class="bg-blob"></div>
    <div class="bg-blob"></div>
    <div class="bg-blob"></div>
  </div>

  <ToastContainer ref="toastRef" />

  <div id="app">
    <AppHeader @toggle-admin="showAdminPanel = true" />

    <StatsRow
      :total-types="totalTypes"
      :durable-count="durableCount"
      :consumable-count="consumableCount"
      :available-count="availableCount"
    />

    <div class="card-grid">
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

    <HistorySection :history="recentHistory" />
    <footer class="footer">© 2026 一站式物资管理系统 · 数据为虚拟数据</footer>
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
  />
</template>

<script setup>
import { ref, computed } from 'vue'
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
import ToastContainer from './components/ToastContainer.vue'
import QRCode from 'qrcode'

const {
  allMaterials, durableMaterials, consumableMaterials,
  totalTypes, durableCount, consumableCount, availableCount, recentHistory,
  getRemaining, getMaterial, getAvailableItems, getBorrowedItems,
  borrowItem, borrowIndividualItem, returnItem, returnIndividualItem,
  updateTotalQuantity, updateThreshold, addRemoteItems, removeRemoteItem,
  verifyPassword
} = useStore()

const toastRef = ref(null)
function toast(msg, type = 'info') { toastRef.value?.show(msg, type) }

// Borrow modal
const borrowModalVisible = ref(false)
const borrowMaterial = ref(null)
const borrowRemaining = ref(0)
const borrowAvailableItems = ref([])

function openBorrowModal(materialId) {
  const m = getMaterial(materialId)
  if (!m) return
  borrowMaterial.value = m
  borrowRemaining.value = getRemaining(m)
  borrowAvailableItems.value = getAvailableItems(materialId)
  borrowModalVisible.value = true
}

function handleBorrow({ materialId, borrower, itemCode, quantity }) {
  const m = getMaterial(materialId)
  if (!m) return
  if (m.hasIndividualTracking) {
    if (!itemCode) { toast('没有可用的遥控器', 'error'); return }
    const result = borrowIndividualItem(materialId, itemCode, borrower)
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) borrowModalVisible.value = false
  } else {
    if (!borrower?.trim()) { toast('请输入借用人姓名', 'error'); return }
    const result = borrowItem(materialId, quantity, borrower.trim())
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) borrowModalVisible.value = false
  }
}

// Return modal
const returnModalVisible = ref(false)
const returnMaterial = ref(null)
const returnBorrowedItems = ref([])

function openReturnModal(materialId) {
  const m = getMaterial(materialId)
  if (!m) return
  returnMaterial.value = m
  returnBorrowedItems.value = getBorrowedItems(materialId)
  returnModalVisible.value = true
}

function handleReturn({ materialId, returner, itemCode, quantity }) {
  const m = getMaterial(materialId)
  if (!m) return
  if (m.hasIndividualTracking) {
    if (!itemCode) { toast('没有已借出的遥控器', 'error'); return }
    const result = returnIndividualItem(materialId, itemCode, returner)
    toast(result.msg, result.ok ? 'success' : 'error')
    if (result.ok) returnModalVisible.value = false
  } else {
    const result = returnItem(materialId, quantity, returner)
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

function printQR(itemCode) {
  const canvas = document.createElement('canvas')
  QRCode.toCanvas(canvas, `MATERIAL:ac-remote:${itemCode}`, {
    width: 250,
    color: { dark: '#1a2332', light: '#ffffff' }
  }).then(() => {
    const dataUrl = canvas.toDataURL('image/png')
    const w = window.open('', '_blank', 'width=400,height=500')
    w.document.write(`<!DOCTYPE html><html><head><title>打印二维码 - ${itemCode}</title><style>body{text-align:center;padding:30px;font-family:sans-serif;}img{border:2px dashed #ddd;padding:10px;}</style></head><body><h2>🔑 ${itemCode}</h2><p>空调遥控器 - 专属二维码</p><img src="${dataUrl}" width="250" height="250"><p style="margin-top:16px;font-size:13px;color:#888;">扫描二维码进行借出登记</p></body></html>`)
    w.document.close()
    setTimeout(() => w.print(), 400)
  })
}

function printAllQR() {
  const m = getMaterial('ac-remote')
  if (!m?.items) return
  const w = window.open('', '_blank', 'width=900,height=700')
  w.document.write(`<!DOCTYPE html><html><head><title>打印全部二维码</title><style>body{font-family:sans-serif;padding:20px;}h2{text-align:center;}.subtitle{text-align:center;color:#666;font-size:14px;margin-bottom:20px;}.qr-grid{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;}.qr-item{text-align:center;width:180px;padding:12px;border:1px dashed #ddd;border-radius:8px;}.qr-item .code{font-weight:bold;margin-bottom:6px;}@media print{.qr-item{page-break-inside:avoid;}}</style></head><body><h2>${m.icon} ${m.name} - 二维码清单</h2><p class="subtitle">共 ${m.items.length} 个遥控器</p><div class="qr-grid" id="printQrGrid"></div></body></html>`)
  w.document.close()
  setTimeout(() => {
    const grid = w.document.getElementById('printQrGrid')
    m.items.forEach(i => {
      const div = w.document.createElement('div')
      div.className = 'qr-item'
      div.innerHTML = `<div class="code">🔑 ${i.code}</div>`
      grid.appendChild(div)
      const cv = w.document.createElement('canvas')
      QRCode.toCanvas(cv, `MATERIAL:ac-remote:${i.code}`, { width: 130, color: { dark: '#1a2332', light: '#ffffff' } }).then(() => div.appendChild(cv))
    })
    setTimeout(() => w.print(), 800)
  }, 300)
}

// Add remote
const showAddRemoteModal = ref(false)
const nextRemoteNum = computed(() => {
  const m = getMaterial('ac-remote')
  if (!m?.items) return 1
  return m.items.reduce((max, i) => {
    const match = i.code.match(/\d+$/)
    return match ? Math.max(max, parseInt(match[0], 10)) : max
  }, 0) + 1
})

function handleAddRemotes({ prefix, startNum, count }) {
  if (isNaN(startNum) || startNum < 1) { toast('请输入有效的起始编号', 'error'); return }
  if (isNaN(count) || count < 1 || count > 50) { toast('添加数量需在 1~50 之间', 'error'); return }
  const result = addRemoteItems('ac-remote', prefix, startNum, count)
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

function handleItemBorrow({ itemCode, borrower }) {
  const result = borrowIndividualItem('ac-remote', itemCode, borrower)
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) itemBorrowModalVisible.value = false
}

// Item return
const itemReturnModalVisible = ref(false)
const itemReturnCode = ref('')
const itemReturnCurrentBorrower = ref('')

function openItemReturnModal(itemCode) {
  const m = getMaterial('ac-remote')
  const item = m?.items?.find(i => i.code === itemCode)
  if (!item) { toast(`遥控器 ${itemCode} 未被借出`, 'error'); return }
  itemReturnCode.value = itemCode
  itemReturnCurrentBorrower.value = item.borrowedBy || '未知'
  itemReturnModalVisible.value = true
}

function handleItemReturn({ itemCode, returner }) {
  const result = returnIndividualItem('ac-remote', itemCode, returner)
  toast(result.msg, result.ok ? 'success' : 'error')
  if (result.ok) itemReturnModalVisible.value = false
}

// Delete item
function handleDeleteItem(itemCode) {
  if (!confirm(`确定要删除遥控器 ${itemCode} 吗？此操作不可恢复。`)) return
  const result = removeRemoteItem('ac-remote', itemCode)
  toast(result.msg, result.ok ? 'success' : 'error')
}

// Admin
const showAdminPanel = ref(false)
const adminLoggedIn = ref(false)

function handleAdminLogin(password) {
  if (verifyPassword(password)) {
    adminLoggedIn.value = true
    toast('管理员验证成功', 'success')
  } else {
    toast('密码错误', 'error')
  }
}

function handleAdminLogout() { adminLoggedIn.value = false }

function handleSaveTotal(materialId, newTotal) {
  const result = updateTotalQuantity(materialId, newTotal)
  toast(result.msg, result.ok ? 'success' : 'error')
}

function handleSaveThreshold(materialId, newThreshold) {
  const result = updateThreshold(materialId, newThreshold)
  toast(result.msg, result.ok ? 'success' : 'error')
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
})
</script>
