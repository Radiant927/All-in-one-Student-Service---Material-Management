<template>
  <view class="page">
    <view class="card search-box"><input v-model="search" placeholder="搜索物资名称" @confirm="loadMaterials"><button size="mini" @click="loadMaterials">搜索</button></view>
    <view v-for="item in materials" :key="item.id" class="card material" @click="openMaterial(item.id)">
      <text class="icon">{{ item.icon || '📦' }}</text>
      <view class="info"><text class="name">{{ item.name }}</text><text class="muted">{{ item.spec || '暂无规格' }}</text></view>
      <view class="stock"><text>{{ item.available_quantity }}</text><text class="muted">可申请</text></view>
    </view>
    <view v-if="!loading && materials.length === 0" class="card muted">未找到物资</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { request, requireLogin } from '../../services/request.js'
const materials = ref([]); const search = ref(''); const loading = ref(false)
async function loadMaterials() { if (!requireLogin()) return; loading.value=true; try { const q=search.value ? `?search=${encodeURIComponent(search.value)}` : ''; materials.value=await request(`/materials${q}`) } finally { loading.value=false } }
function openMaterial(id) { uni.navigateTo({ url:`/pages/material-detail/index?id=${id}` }) }
onShow(loadMaterials)
</script>

<style scoped>
.search-box,.material { display:flex; align-items:center; gap:20rpx; }.search-box input { flex:1; }.icon { font-size:54rpx; }.info { flex:1; }.name,.stock text { display:block; font-weight:600; }.stock { text-align:right; }.stock>text:first-child { color:#4f46e5; font-size:36rpx; }
</style>

