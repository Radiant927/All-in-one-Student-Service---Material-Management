<template>
  <view class="page"><view v-for="item in rows" :key="item.id" class="card"><view class="row"><text class="name">{{ item.material_name }}</text><text class="status">{{ label(item.status) }}</text></view><text class="muted">申请 {{ item.quantity }} 件 · {{ formatTime(item.created_at) }}</text><text v-if="item.review_note" class="note">审核备注：{{ item.review_note }}</text><button v-if="item.status==='picked_up'" size="mini" @click="requestReturn(item)">发起归还</button><button v-if="['submitted','approved'].includes(item.status)" size="mini" @click="cancel(item)">取消申请</button></view><view v-if="rows.length===0" class="card muted">暂无申请记录</view></view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request, requireLogin } from '../../services/request.js'
import { applicationStatusLabel } from '../../constants/applicationStatus.js'
const rows=ref([])
const label=applicationStatusLabel; const formatTime=value=>new Date(value).toLocaleString()
async function load(){ if(!requireLogin())return; const data=await request('/borrow-applications/mine'); rows.value=data.rows||[] }
async function requestReturn(item){ await request(`/borrow-applications/${item.id}/request-return`,{method:'POST'}); uni.showToast({title:'已发起归还'}); load() }
async function cancel(item){ await request(`/borrow-applications/${item.id}/cancel`,{method:'POST'}); uni.showToast({title:'已取消'}); load() }
onShow(load)
</script>

<style scoped>.row { display:flex; justify-content:space-between; align-items:center; }.name { font-weight:700; }.muted,.note { display:block; margin:14rpx 0; }.note { font-size:25rpx; }</style>
