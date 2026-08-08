<template>
  <view class="page"><view class="card scan-card"><text class="scan-icon">▣</text><text>扫描物资二维码，快速查看并申请</text><button class="primary" @click="scan">开始扫码</button></view><view v-if="result" class="card"><text class="name">{{ result.material.name }}</text><text class="muted">可申请 {{ result.material.available_quantity }}</text><button @click="openDetail">查看详情</button></view></view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request, requireLogin } from '../../services/request.js'
const result=ref(null); onShow(requireLogin)
async function scan(){ const scanResult=await new Promise((resolve,reject)=>uni.scanCode({success:resolve,fail:reject})); result.value=await request('/scan/resolve',{method:'POST',data:{payload:scanResult.result}}) }
function openDetail(){ uni.navigateTo({url:`/pages/material-detail/index?id=${result.value.material.id}`}) }
</script>

<style scoped>.scan-card { text-align:center; }.scan-card text { display:block; margin:24rpx; }.scan-icon { font-size:120rpx; color:#4f46e5; }.name { display:block; font-size:34rpx; font-weight:700; }</style>

