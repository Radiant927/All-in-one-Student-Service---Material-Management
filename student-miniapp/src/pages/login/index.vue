<template>
  <view class="page login-page">
    <view class="hero">📦</view>
    <view class="card">
      <text class="title">一站式物资服务</text>
      <text class="muted intro">通过学校统一认证查询物资并提交借用申请</text>
      <button class="primary" :loading="loading" @click="schoolLogin">学校统一认证登录</button>
      <view v-if="isDevelopment" class="dev-box">
        <text class="muted">开发环境模拟认证</text>
        <input v-model="studentNo" class="field" placeholder="测试学号">
        <input v-model="name" class="field" placeholder="测试姓名">
        <button @click="mockLogin">模拟学生登录</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { request, saveTokens } from '../../services/request.js'

const loading = ref(false)
const studentNo = ref('20260001')
const name = ref('测试学生')
const isDevelopment = import.meta.env.DEV

async function finishLogin(data) {
  saveTokens(data)
  uni.switchTab({ url: '/pages/home/index' })
}

async function schoolLogin() {
  loading.value = true
  try {
    const loginResult = await new Promise((resolve, reject) => uni.login({ provider: 'weixin', success: resolve, fail: reject }))
    await finishLogin(await request('/auth/login', { method: 'POST', data: { credential: loginResult.code } }))
  } finally { loading.value = false }
}

async function mockLogin() {
  loading.value = true
  try {
    const data = await request('/auth/login', {
      method: 'POST',
      data: {
        external_subject: `mock:${studentNo.value}`,
        student_no: studentNo.value,
        name: name.value,
        role: 'student',
      },
    })
    await finishLogin(data)
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { padding-top:120rpx; }.hero { font-size:100rpx; text-align:center; margin-bottom:30rpx; }.title { display:block; text-align:center; font-size:42rpx; font-weight:700; }.intro { display:block; text-align:center; margin:20rpx 0 40rpx; }.dev-box { border-top:1px solid #e2e8f0; margin-top:36rpx; padding-top:28rpx; }
</style>

