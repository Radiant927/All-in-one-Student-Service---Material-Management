<template>
  <Teleport to="body">
    <div class="admin-overlay" :class="{ active: visible }" @click.self="$emit('close')"></div>
    <div class="admin-panel" :class="{ active: visible }">
      <div class="admin-panel-header">
        <span class="admin-panel-title">⚙️ 管理员设置</span>
        <button class="modal-close" @click="$emit('close')">✕</button>
      </div>
      <div class="admin-panel-body">
        <div v-if="!loggedIn" class="admin-password-section">
          <p class="desc">请输入管理员密码</p>
          <input
            class="form-input" type="password" v-model="password"
            placeholder="管理员密码" @keydown.enter="login">
          <p class="password-error" :class="{ visible: errorVisible }">⚠️ 密码错误，请重试</p>
          <button class="btn-primary" @click="login" :disabled="loggingIn" style="margin-top:6px;">
            {{ loggingIn ? '验证中...' : '验证登录' }}
          </button>
          <p class="hint">默认密码: admin888</p>
        </div>
        <div v-else>
          <h3>📝 物资数量管理</h3>
          <div v-for="m in materials" :key="m.id" class="admin-material-item">
            <div class="admin-material-name">
              {{ m.icon }} {{ m.name }}
              <span class="admin-info">
                <template v-if="m.has_individual_tracking">
                  (共{{ m.totalQuantity || 0 }}个, 剩余{{ getRemaining(m) }}, 已借出{{ m.borrowedQuantity || 0 }})
                </template>
                <template v-else>
                  (剩余: {{ getRemaining(m) }})
                </template>
              </span>
            </div>
            <p v-if="m.has_individual_tracking" class="tip">💡 通过管理页面添加/删除遥控器代号来调整数量</p>
            <div v-if="!m.has_individual_tracking" class="admin-row">
              <label>总数量</label>
              <input type="number" v-model.number="editValues[m.id].total" :min="m.borrowedQuantity || 0">
              <button class="btn-save-admin" @click="$emit('save-total', m.id, editValues[m.id].total)">保存</button>
            </div>
            <div class="admin-row">
              <label>低库存阈值</label>
              <input type="number" v-model.number="editValues[m.id].threshold" min="0">
              <button class="btn-save-admin" @click="$emit('save-threshold', m.id, editValues[m.id].threshold)">保存</button>
            </div>
          </div>

          <h3 style="margin-top:20px;">🔧 工具</h3>
          <div class="admin-tools">
            <button class="btn-tool" @click="$emit('toggle-locations')">📍 储位管理</button>
            <button class="btn-tool" @click="$emit('toggle-import')">📥 导入 Excel</button>
          </div>

          <h3 style="margin-top:20px;">📧 邮件通知设置</h3>
          <div class="admin-material-item">
            <div class="admin-row">
              <label>SMTP服务器</label>
              <input v-model="smtpConfig.host" placeholder="smtp.qq.com">
            </div>
            <div class="admin-row">
              <label>端口</label>
              <input type="number" v-model.number="smtpConfig.port" placeholder="587">
            </div>
            <div class="admin-row">
              <label>用户名</label>
              <input v-model="smtpConfig.user" placeholder="邮箱地址">
            </div>
            <div class="admin-row">
              <label>授权码</label>
              <input type="password" v-model="smtpConfig.pass" placeholder="SMTP授权码">
            </div>
            <div class="admin-row">
              <label>发件人</label>
              <input v-model="smtpConfig.from" placeholder="发件邮箱">
            </div>
            <div class="admin-row">
              <label>收件人</label>
              <input v-model="smtpConfig.to" placeholder="采购负责人邮箱">
            </div>
            <div class="admin-row-btns">
              <button class="btn-save-admin" @click="saveSmtp">💾 保存</button>
              <button class="btn-test-email" @click="showTestEmail = true" :disabled="!smtpConfig.host">📧 测试</button>
            </div>
            <div v-if="showTestEmail" class="test-email-row">
              <input v-model="testEmailAddr" placeholder="输入测试收件邮箱" class="form-input" style="flex:1">
              <button class="btn-save-admin" @click="sendTest" :disabled="sendingTest">发送</button>
              <button class="btn-cancel" @click="showTestEmail = false">取消</button>
            </div>
            <p v-if="smtpMsg" class="smtp-msg" :class="smtpOk ? 'ok' : 'err'">{{ smtpMsg }}</p>
          </div>

          <button class="btn-logout" @click="$emit('logout')">🚪 退出管理</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { fetchSettings, updateSettings, testEmail } from '../api/admin.js'

const props = defineProps({
  visible: Boolean,
  loggedIn: Boolean,
  materials: Array
})

const emit = defineEmits(['close', 'login', 'logout', 'save-total', 'save-threshold', 'toggle-locations', 'toggle-import'])

const password = ref('')
const errorVisible = ref(false)
const loggingIn = ref(false)

const editValues = reactive({})

// SMTP config
const smtpConfig = reactive({
  host: '', port: 587, user: '', pass: '', from: '', to: ''
})
const showTestEmail = ref(false)
const testEmailAddr = ref('')
const sendingTest = ref(false)
const smtpMsg = ref('')
const smtpOk = ref(false)

async function loadSmtpSettings() {
  const res = await fetchSettings()
  if (res.ok && res.data) {
    smtpConfig.host = res.data.smtp_host || ''
    smtpConfig.port = parseInt(res.data.smtp_port) || 587
    smtpConfig.user = res.data.smtp_user || ''
    smtpConfig.pass = res.data.smtp_pass || ''
    smtpConfig.from = res.data.smtp_from || ''
    smtpConfig.to = res.data.smtp_to || ''
  }
}

async function saveSmtp() {
  const data = {
    smtp_host: smtpConfig.host,
    smtp_port: String(smtpConfig.port),
    smtp_user: smtpConfig.user,
    smtp_pass: smtpConfig.pass,
    smtp_from: smtpConfig.from,
    smtp_to: smtpConfig.to,
  }
  const res = await updateSettings(data)
  smtpMsg.value = res.ok ? 'SMTP设置已保存' : '保存失败'
  smtpOk.value = res.ok
  setTimeout(() => { smtpMsg.value = '' }, 3000)
}

async function sendTest() {
  if (!testEmailAddr.value) return
  sendingTest.value = true
  const res = await testEmail(testEmailAddr.value)
  smtpMsg.value = res.msg
  smtpOk.value = res.ok
  sendingTest.value = false
  setTimeout(() => { smtpMsg.value = '' }, 4000)
}

watch(() => props.visible, (v) => {
  if (v) {
    password.value = ''
    errorVisible.value = false
    loggingIn.value = false
    showTestEmail.value = false
    testEmailAddr.value = ''
    smtpMsg.value = ''
    props.materials.forEach(m => {
      editValues[m.id] = {
        total: m.totalQuantity || 0,
        threshold: m.low_stock_threshold || 0
      }
    })
    if (props.loggedIn) loadSmtpSettings()
  }
})

// 登录成功后加载 SMTP 设置（面板已打开时）
watch(() => props.loggedIn, (val) => {
  if (val && props.visible) loadSmtpSettings()
})

async function login() {
  loggingIn.value = true
  emit('login', password.value)
  errorVisible.value = true
  setTimeout(() => { errorVisible.value = false }, 1500)
  setTimeout(() => { loggingIn.value = false }, 500)
}

function getRemaining(m) {
  if (m.has_individual_tracking && m.items) {
    return m.items.filter(i => i.status === 'available').length
  }
  return Math.max(0, (m.totalQuantity || 0) - (m.borrowedQuantity || 0))
}
</script>

<style scoped>
.admin-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(15,20,30,0.35);
  opacity: 0; pointer-events: none; transition: opacity 0.3s;
}
.admin-overlay.active { opacity: 1; pointer-events: auto; }
.admin-panel {
  position: fixed; top: 0; right: 0; width: 400px; max-width: 92vw;
  height: 100vh; z-index: 201; background: #fff;
  box-shadow: -8px 0 40px rgba(0,0,0,0.12);
  transform: translateX(100%); transition: transform 0.35s;
  display: flex; flex-direction: column; overflow-y: auto;
}
.admin-panel.active { transform: translateX(0); }
.admin-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 22px; border-bottom: 1px solid #eef1f5; }
.admin-panel-title { font-size: 1.1rem; font-weight: 700; }
.modal-close {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: #f1f5f9; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  color: #5a6b7d; transition: all 0.3s;
}
.modal-close:hover { background: #e2e8f0; color: #1a2332; }
.admin-panel-body { padding: 20px 22px; flex: 1; }
.admin-panel-body h3 { font-size: 0.9rem; color: #5a6b7d; margin-bottom: 14px; }
.admin-password-section { text-align: center; padding-top: 20px; }
.desc { color: #5a6b7d; font-size: 0.88rem; margin-bottom: 14px; }
.hint { font-size: 0.72rem; color: #8e9aab; margin-top: 10px; }
.password-error { color: #dc2626; font-size: 0.8rem; margin-top: 6px; display: none; }
.password-error.visible { display: block; }
.admin-material-item { background: #f8fafc; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #eef1f5; }
.admin-material-name { font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
.admin-info { font-size: 0.75rem; color: #8e9aab; }
.tip { font-size: 0.75rem; color: #8e9aab; margin-bottom: 8px; }
.admin-row { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
.admin-row:last-child { margin-bottom: 0; }
.admin-row label { font-size: 0.78rem; color: #5a6b7d; white-space: nowrap; min-width: 56px; }
.admin-row input {
  flex: 1; padding: 8px 10px; border-radius: 8px;
  border: 1.5px solid #dde4ed; font-size: 0.85rem; outline: none; transition: all 0.3s;
}
.admin-row input:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.08); }
.btn-save-admin {
  padding: 8px 16px; border-radius: 8px; border: none;
  background: #667eea; color: #fff; font-size: 0.8rem;
  font-weight: 600; cursor: pointer; transition: all 0.3s; white-space: nowrap;
}
.btn-save-admin:hover { background: #4c63d2; }
.admin-tools { display: flex; gap: 10px; margin-bottom: 16px; }
.btn-tool {
  flex: 1; padding: 10px; border-radius: 10px; border: 1.5px solid #dde4ed;
  background: #fff; cursor: pointer; font-size: 0.84rem;
  font-weight: 600; color: #5a6b7d; transition: all 0.3s;
}
.btn-tool:hover { border-color: #667eea; color: #667eea; background: #f8faff; }
.btn-logout {
  margin-top: 16px; width: 100%; padding: 10px;
  border-radius: 10px; border: 1.5px solid #dde4ed;
  background: #fff; cursor: pointer; font-size: 0.88rem;
  font-weight: 600; color: #5a6b7d; transition: all 0.3s;
}
.btn-logout:hover { background: #fef2f2; border-color: #fecaca; color: #dc2626; }
.form-input {
  width: 100%; padding: 11px 14px; border-radius: 10px;
  border: 1.5px solid #dde4ed; font-size: 0.93rem;
  color: #1a2332; background: #f8fafc; transition: all 0.3s; outline: none;
}
.form-input:focus { border-color: #667eea; background: #fff; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
.btn-primary {
  width: 100%; padding: 12px; border-radius: 25px; border: none;
  background: linear-gradient(135deg, #667eea, #4facfe);
  color: #fff; font-size: 0.95rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 14px rgba(102,126,234,0.3);
  transition: all 0.3s;
}
.btn-primary:hover { box-shadow: 0 6px 22px rgba(102,126,234,0.45); transform: translateY(-1px); }
.btn-primary:disabled { background: #ccd0d8; box-shadow: none; cursor: not-allowed; transform: none; }

.admin-row-btns { display: flex; gap: 8px; margin-top: 6px; }
.btn-test-email {
  padding: 8px 16px; border-radius: 8px; border: 1.5px solid #dde4ed;
  background: #fff; font-size: 0.8rem; font-weight: 600;
  cursor: pointer; color: #5a6b7d; transition: all 0.3s; white-space: nowrap;
}
.btn-test-email:hover:not(:disabled) { border-color: #667eea; color: #667eea; }
.btn-test-email:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel {
  padding: 8px 12px; border-radius: 8px; border: none;
  background: #f1f5f9; font-size: 0.8rem; cursor: pointer;
  color: #5a6b7d; white-space: nowrap;
}
.btn-cancel:hover { background: #e2e8f0; }
.test-email-row { display: flex; gap: 8px; align-items: center; margin-top: 10px; }
.smtp-msg { font-size: 0.78rem; margin-top: 8px; padding: 6px 10px; border-radius: 8px; }
.smtp-msg.ok { color: #059669; background: #d1fae5; }
.smtp-msg.err { color: #dc2626; background: #fef2f2; }
</style>