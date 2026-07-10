<template>
  <Teleport to="body">
    <div class="qr-modal-overlay" :class="{ active: visible }" @click.self="$emit('close')">
      <div class="qr-modal-content">
        <div class="modal-header">
          <span class="modal-title">🔳 遥控器二维码</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="qr-code-title">{{ itemCode }}</div>
        <div class="qr-code-subtitle">空调遥控器</div>
        <div class="qr-code-container" ref="qrContainer"></div>
        <p class="qr-hint">💡 可右键保存二维码图片，或直接打印贴到遥控器上</p>
        <button class="btn-primary" @click="$emit('print-qr', itemCode)" style="margin-top:12px;">🖨️ 打印此二维码</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import QRCode from 'qrcode'

const props = defineProps({
  visible: Boolean,
  itemCode: String
})

defineEmits(['close', 'print-qr'])

const qrContainer = ref(null)

watch(() => props.visible, async (v) => {
  if (v && props.itemCode) {
    await nextTick()
    if (qrContainer.value) {
      qrContainer.value.innerHTML = ''
      try {
        const canvas = document.createElement('canvas')
        await QRCode.toCanvas(canvas, `MATERIAL:ac-remote:${props.itemCode}`, {
          width: 200,
          color: { dark: '#1a2332', light: '#ffffff' }
        })
        qrContainer.value.appendChild(canvas)
      } catch {
        qrContainer.value.innerHTML = '<div style="padding:40px;color:#999;">二维码生成失败</div>'
      }
    }
  }
})
</script>

<style scoped>
.qr-modal-overlay {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(15,20,30,0.5); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.25s;
}
.qr-modal-overlay.active { opacity: 1; pointer-events: auto; }
.qr-modal-content {
  background: #fff; border-radius: 22px; padding: 28px;
  text-align: center; box-shadow: 0 24px 64px rgba(0,0,0,0.2);
  transform: scale(0.92); transition: transform 0.25s;
  max-width: 380px; width: 92%;
}
.qr-modal-overlay.active .qr-modal-content { transform: scale(1); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-title { font-size: 1.15rem; font-weight: 700; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }
.qr-code-title { font-size: 1rem; font-weight: 700; margin-bottom: 4px; }
.qr-code-subtitle { font-size: 0.8rem; color: #8e9aab; margin-bottom: 8px; }
.qr-code-container { display: inline-block; padding: 20px; background: #fff; border: 2px dashed #dde4ed; border-radius: 12px; margin: 16px 0; }
.qr-hint { font-size: 0.78rem; color: #8e9aab; margin-top: 10px; }
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
</style>
