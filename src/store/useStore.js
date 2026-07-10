import { reactive, computed } from 'vue'

function generateItems(prefix, count, startNum) {
  const items = []
  const padLen = Math.max(3, String(startNum + count - 1).length)
  for (let i = 0; i < count; i++) {
    const num = String(startNum + i).padStart(padLen, '0')
    items.push({
      code: prefix + '-' + num,
      status: 'available',
      borrowedBy: null,
      borrowTime: null
    })
  }
  return items
}

const state = reactive({
  materials: [
    {
      id: 'ac-remote',
      name: '空调遥控器',
      icon: '🎮',
      type: 'durable',
      lowStockThreshold: 3,
      colorIdx: 0,
      hasIndividualTracking: true,
      items: generateItems('AC', 20, 1)
    },
    {
      id: 'water',
      name: '饮用水',
      icon: '💧',
      type: 'consumable',
      totalQuantity: 50,
      borrowedQuantity: 12,
      lowStockThreshold: 5,
      colorIdx: 1
    },
    {
      id: 'tissues',
      name: '纸巾',
      icon: '🧻',
      type: 'consumable',
      totalQuantity: 100,
      borrowedQuantity: 30,
      lowStockThreshold: 10,
      colorIdx: 2
    },
    {
      id: 'pens',
      name: '笔',
      icon: '🖊️',
      type: 'consumable',
      totalQuantity: 60,
      borrowedQuantity: 18,
      lowStockThreshold: 10,
      colorIdx: 3
    }
  ],
  borrowHistory: [],
  adminPassword: 'admin888',
  adminLoggedIn: false
})

function syncQuantities(m) {
  if (m.hasIndividualTracking && m.items) {
    m.totalQuantity = m.items.length
    m.borrowedQuantity = m.items.filter(i => i.status === 'borrowed').length
  }
}

function addHistory(materialId, action, quantity, borrower, returnedBy, itemCode) {
  state.borrowHistory.push({
    id: Date.now(),
    materialId,
    action,
    quantity,
    borrower: borrower || null,
    returnedBy: returnedBy || null,
    itemCode: itemCode || null,
    timestamp: new Date().toISOString()
  })
  if (state.borrowHistory.length > 200) {
    state.borrowHistory = state.borrowHistory.slice(-200)
  }
}

export function useStore() {
  // --- Getters ---
  const allMaterials = computed(() => {
    state.materials.forEach(m => syncQuantities(m))
    return state.materials
  })

  const durableMaterials = computed(() =>
    allMaterials.value.filter(m => m.type === 'durable')
  )

  const consumableMaterials = computed(() =>
    allMaterials.value.filter(m => m.type === 'consumable')
  )

  const totalTypes = computed(() => allMaterials.value.length)

  const durableCount = computed(() =>
    durableMaterials.value.reduce((s, m) => s + (m.items ? m.items.length : m.totalQuantity), 0)
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

  // --- Helpers ---
  function getRemaining(m) {
    syncQuantities(m)
    if (m.hasIndividualTracking && m.items) {
      return m.items.filter(i => i.status === 'available').length
    }
    return Math.max(0, (m.totalQuantity || 0) - (m.borrowedQuantity || 0))
  }

  function getMaterial(id) {
    return allMaterials.value.find(m => m.id === id)
  }

  function getAvailableItems(materialId) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return []
    return m.items.filter(i => i.status === 'available')
  }

  function getBorrowedItems(materialId) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return []
    return m.items.filter(i => i.status === 'borrowed')
  }

  // --- Actions ---
  function borrowItem(materialId, quantity, borrower) {
    const m = getMaterial(materialId)
    if (!m) return { ok: false, msg: '物资不存在' }
    const remaining = getRemaining(m)
    if (quantity > remaining) return { ok: false, msg: `库存不足，仅剩 ${remaining} 个` }
    if (quantity <= 0) return { ok: false, msg: '借用数量必须大于0' }
    m.borrowedQuantity = (m.borrowedQuantity || 0) + quantity
    addHistory(materialId, 'borrow', quantity, borrower, null, null)
    return { ok: true, msg: `成功借出 ${quantity} 个${m.name}` }
  }

  function borrowIndividualItem(materialId, itemCode, borrower) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return { ok: false, msg: '物资不存在' }
    const item = m.items.find(i => i.code === itemCode)
    if (!item) return { ok: false, msg: `遥控器 ${itemCode} 不存在` }
    if (item.status === 'borrowed') return { ok: false, msg: `遥控器 ${itemCode} 已被借出` }
    if (!borrower || !borrower.trim()) return { ok: false, msg: '请输入借用人姓名' }
    item.status = 'borrowed'
    item.borrowedBy = borrower.trim()
    item.borrowTime = new Date().toISOString()
    syncQuantities(m)
    addHistory(materialId, 'borrow', 1, borrower.trim(), null, itemCode)
    return { ok: true, msg: `成功借出遥控器 ${itemCode}` }
  }

  function returnItem(materialId, quantity, returnedBy) {
    const m = getMaterial(materialId)
    if (!m) return { ok: false, msg: '物资不存在' }
    if (quantity > (m.borrowedQuantity || 0)) return { ok: false, msg: `归还数量超过已借出数量` }
    if (quantity <= 0) return { ok: false, msg: '归还数量必须大于0' }
    m.borrowedQuantity -= quantity
    addHistory(materialId, 'return', quantity, null, returnedBy || null, null)
    return { ok: true, msg: `成功归还 ${quantity} 个${m.name}` }
  }

  function returnIndividualItem(materialId, itemCode, returnedBy) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return { ok: false, msg: '物资不存在' }
    const item = m.items.find(i => i.code === itemCode)
    if (!item) return { ok: false, msg: `遥控器 ${itemCode} 不存在` }
    if (item.status === 'available') return { ok: false, msg: `遥控器 ${itemCode} 未被借出` }
    if (!returnedBy || !returnedBy.trim()) return { ok: false, msg: '请输入归还人姓名' }
    item.status = 'available'
    item.borrowedBy = null
    item.borrowTime = null
    syncQuantities(m)
    addHistory(materialId, 'return', 1, item.borrowedBy, returnedBy.trim(), itemCode)
    return { ok: true, msg: `成功归还遥控器 ${itemCode}` }
  }

  function updateTotalQuantity(materialId, newTotal) {
    const m = getMaterial(materialId)
    if (!m) return { ok: false, msg: '物资不存在' }
    if (m.hasIndividualTracking) return { ok: false, msg: '请通过管理页面调整遥控器数量' }
    const val = parseInt(newTotal, 10)
    if (isNaN(val) || val < 0) return { ok: false, msg: '请输入有效数量' }
    if (val < (m.borrowedQuantity || 0)) return { ok: false, msg: `总数不能小于已借出数量` }
    m.totalQuantity = val
    return { ok: true, msg: `${m.name} 总数已更新为 ${val}` }
  }

  function updateThreshold(materialId, newThreshold) {
    const m = getMaterial(materialId)
    if (!m) return { ok: false, msg: '物资不存在' }
    const val = parseInt(newThreshold, 10)
    if (isNaN(val) || val < 0) return { ok: false, msg: '请输入有效阈值' }
    m.lowStockThreshold = val
    return { ok: true, msg: `${m.name} 低库存阈值已更新为 ${val}` }
  }

  function addRemoteItems(materialId, prefix, startNum, count) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return { ok: false, msg: '该物资不支持个体追踪' }
    const newItems = generateItems(prefix, count, startNum)
    for (const ni of newItems) {
      if (m.items.some(i => i.code === ni.code)) {
        return { ok: false, msg: `代号 ${ni.code} 已存在` }
      }
    }
    m.items.push(...newItems)
    syncQuantities(m)
    return { ok: true, msg: `成功添加 ${count} 个遥控器 (${newItems[0].code} ~ ${newItems[newItems.length - 1].code})` }
  }

  function removeRemoteItem(materialId, itemCode) {
    const m = getMaterial(materialId)
    if (!m || !m.items) return { ok: false, msg: '该物资不支持个体追踪' }
    const item = m.items.find(i => i.code === itemCode)
    if (!item) return { ok: false, msg: `遥控器 ${itemCode} 不存在` }
    if (item.status === 'borrowed') return { ok: false, msg: `遥控器 ${itemCode} 已被借出，请先归还再删除` }
    m.items = m.items.filter(i => i.code !== itemCode)
    syncQuantities(m)
    return { ok: true, msg: `已删除遥控器 ${itemCode}` }
  }

  function verifyPassword(pw) {
    return pw === state.adminPassword
  }

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
    borrowItem,
    borrowIndividualItem,
    returnItem,
    returnIndividualItem,
    updateTotalQuantity,
    updateThreshold,
    addRemoteItems,
    removeRemoteItem,
    verifyPassword
  }
}
