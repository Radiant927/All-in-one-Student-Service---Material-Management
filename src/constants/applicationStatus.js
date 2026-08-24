export const applicationStatusLabels = Object.freeze({
  submitted: '待审核',
  approved: '待领取',
  picked_up: '已领取',
  return_pending: '待归还验收',
  returned: '已归还',
  rejected: '已拒绝',
  cancelled: '已取消',
  expired: '已过期',
})

export function applicationStatusLabel(value) {
  return applicationStatusLabels[value] || value
}

