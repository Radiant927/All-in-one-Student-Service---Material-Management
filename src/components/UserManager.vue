<template>
  <Teleport to="body">
    <div v-if="visible" class="overlay" @click.self="$emit('close')">
      <section class="dialog">
        <header><h2>用户与权限</h2><button @click="$emit('close')">✕</button></header>
        <div class="search"><input v-model.trim="search" placeholder="姓名或学号"><button @click="loadUsers">搜索</button></div>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="users">
          <article v-for="user in users" :key="user.id" class="user-row">
            <div><strong>{{ user.name }}</strong><p>{{ user.student_no || user.external_subject }}</p></div>
            <select v-model="user.role" @change="save(user)"><option value="student">学生</option><option value="operator">操作员</option><option value="admin">管理员</option></select>
            <select v-model="user.status" @change="save(user)"><option value="active">启用</option><option value="disabled">停用</option></select>
          </article>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { fetchUsers, updateUser } from '../api/users.js'
const props=defineProps({visible:Boolean,toast:Function}); defineEmits(['close'])
const users=ref([]); const search=ref(''); const error=ref('')
async function loadUsers(){ const result=await fetchUsers({search:search.value}); if(!result.ok){error.value=result.msg;return} error.value='';users.value=result.data?.rows||[] }
async function save(user){ const result=await updateUser(user.id,{role:user.role,status:user.status}); props.toast?.(result.msg,result.ok?'success':'error'); if(!result.ok)loadUsers() }
watch(()=>props.visible,value=>{if(value)loadUsers()})
</script>

<style scoped>
.overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:1200;display:flex;align-items:center;justify-content:center;padding:20px}.dialog{background:#fff;border-radius:18px;width:min(760px,100%);max-height:80vh;overflow:auto;padding:22px}header,.search,.user-row{display:flex;align-items:center;gap:12px}header{justify-content:space-between}.search input{flex:1;padding:10px;border:1px solid #cbd5e1;border-radius:8px}.search button,header button{padding:8px 14px}.users{margin-top:16px;display:grid;gap:10px}.user-row{border:1px solid #e2e8f0;border-radius:12px;padding:12px}.user-row>div{flex:1}.user-row p{margin:4px 0;color:#64748b;font-size:13px}.user-row select{padding:8px;border:1px solid #cbd5e1;border-radius:8px}.error{color:#dc2626}@media(max-width:600px){.user-row{align-items:stretch;flex-direction:column}}
</style>

