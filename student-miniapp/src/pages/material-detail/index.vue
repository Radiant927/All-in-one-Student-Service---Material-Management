<template>
  <view class="page" v-if="material">
    <view class="card"><text class="icon">{{ material.icon || '📦' }}</text><text class="title">{{ material.name }}</text><text class="muted">{{ material.spec || '暂无规格' }}</text></view>
    <view class="card"><view>可申请库存：{{ material.available_quantity }} {{ material.unit }}</view><view>分类：{{ material.category === 'durable' ? '固定性物资' : '消耗性物资' }}</view></view>
    <button class="primary" :disabled="material.available_quantity <= 0" @click="apply">提交借用申请</button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request, requireLogin } from '../../services/request.js'
const material = ref(null)
onLoad(async ({ id }) => { if (requireLogin()) material.value = await request(`/materials/${id}`) })
function apply() { uni.navigateTo({ url:`/pages/application-create/index?materialId=${material.value.id}&name=${encodeURIComponent(material.value.name)}` }) }
</script>

<style scoped>.icon,.title,.muted { display:block; text-align:center; }.icon { font-size:90rpx; }.title { font-size:40rpx; font-weight:700; margin:16rpx; }</style>

