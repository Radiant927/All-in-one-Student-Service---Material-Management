<template>
  <view class="page"><view class="card profile"><text class="avatar">👤</text><text class="name">{{ user.name || '学生' }}</text><text class="muted">{{ user.student_no || '学校统一认证账号' }}</text></view><button @click="logout">退出登录</button></view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { clearTokens, requireLogin } from '../../services/request.js'
const user=ref({})
onShow(()=>{ if(requireLogin()) user.value=uni.getStorageSync('material_user')||{} })
function logout(){ clearTokens(); uni.reLaunch({url:'/pages/login/index'}) }
</script>

<style scoped>.profile { text-align:center; }.profile text { display:block; }.avatar { font-size:100rpx; }.name { font-size:38rpx; font-weight:700; margin:16rpx; }</style>

