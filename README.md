# 一站式物资管理系统

基于 Vue 3 + Vite 构建的前端物资管理系统。

## 功能

- **物资分类管理**：固定性物资（耐用品，支持个体追踪）与消耗性物资
- **借出/归还**：支持按数量借还（消耗品）和按个体代号借还（如空调遥控器）
- **遥控器管理**：独立代号管理、搜索过滤、批量添加/删除
- **二维码**：为每个遥控器生成唯一二维码，支持单个/批量打印
- **借用记录**：可折叠查看历史借还记录
- **管理员面板**：密码登录、修改物资总数和低库存阈值

## 技术栈

- Vue 3 (Composition API + `<script setup>`)
- Vite
- qrcode

## 启动

```bash
npm install
npm run dev
```

浏览器访问 `http://localhost:5173/`

## 构建

```bash
npm run build
npm run preview
```

## 项目结构

```
src/
├── main.js                 # 入口
├── App.vue                 # 根组件
├── style.css               # 全局样式
├── store/
│   └── useStore.js         # 响应式状态管理（虚拟数据）
└── components/
    ├── AppHeader.vue       # 顶部导航
    ├── StatsRow.vue        # 统计面板
    ├── MaterialCard.vue    # 物资卡片
    ├── HistorySection.vue  # 借用记录
    ├── BorrowModal.vue     # 借出弹窗
    ├── ReturnModal.vue     # 归还弹窗
    ├── ManagementPage.vue  # 遥控器管理页面
    ├── QRModal.vue         # 二维码弹窗
    ├── AddRemoteModal.vue  # 添加遥控器
    ├── ItemBorrowModal.vue # 单项借出
    ├── ItemReturnModal.vue # 单项归还
    ├── AdminPanel.vue      # 管理员面板
    └── ToastContainer.vue  # Toast 通知
```
