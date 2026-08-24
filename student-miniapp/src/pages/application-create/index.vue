<template>
  <view class="page"><view class="card"><text class="title">{{ materialName }}</text><input v-model.number="quantity" type="number" class="field" placeholder="申请数量"><input v-model="itemCode" class="field" placeholder="个体代号（仅个体物资填写）"><textarea v-model="purpose" class="field" placeholder="用途说明"></textarea><button class="primary" :loading="submitting" @click="submit">提交申请</button></view></view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { request, requireLogin } from '../../services/request.js'
const materialId=ref(); const materialName=ref('借用申请'); const quantity=ref(1); const itemCode=ref(''); const purpose=ref(''); const submitting=ref(false)
onLoad(options => { requireLogin(); materialId.value=Number(options.materialId); materialName.value=decodeURIComponent(options.name || '借用申请') })
async function submit() { submitting.value=true; try { await request('/borrow-applications',{ method:'POST',data:{ material_id:materialId.value,quantity:Number(quantity.value),item_code:itemCode.value||null,purpose:purpose.value } }); uni.showToast({title:'申请已提交'}); setTimeout(()=>uni.switchTab({url:'/pages/my-applications/index'}),600) } finally { submitting.value=false } }
</script>

<style scoped>.title { display:block; font-size:36rpx; font-weight:700; margin-bottom:20rpx; }textarea.field { width:auto; min-height:160rpx; }</style>

