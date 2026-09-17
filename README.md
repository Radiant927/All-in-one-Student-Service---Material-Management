# 一站式物资管理系统

面向校内物资入库、存储、申请、领用和回收全流程的一站式服务系统，包含 Vue 3 管理端、FastAPI 后端和 uni-app 学生小程序。

## 当前实现状态

- 多仓库、储位、入库、调拨、回收仓优先消耗和个体物资追踪
- PostgreSQL / SQLite、Docker、Alembic 数据迁移和每日数据库备份
- 动态库存预警、补货报表、Excel 导入导出和可配置定时邮件
- 学生、操作员、管理员三类角色，访问令牌、刷新令牌和操作审计
- 借用申请、库存预留、审核、现场领取、归还验收和超时释放闭环
- `MATERIAL:{material_public_id}`、`ITEM:{item_code}` 统一二维码及旧标签兼容
- 无线扫码枪输入页面和微信小程序摄像头扫码
- uni-app 学生端：查询、扫码、提交申请、查看进度、发起归还
- 仓位级库存盘点：快照冲突检测、逐项确认、个体扫码、盘盈盘亏修正及审计留痕

借用申请状态统一为：

```text
submitted → approved → picked_up → return_pending → returned
     └────→ rejected / cancelled        approved → expired
```

审核通过时只预留库存；现场确认领取时才执行 `borrow` 库存流水；归还验收时执行 `return`。

## 业务流程

### 仓储架构

| 仓库类型 | 物理位置 | 存放内容 | 业务规则 |
|---------|---------|---------|---------|
| **主仓库** | 一楼库房 | 全新未拆封物资 | 只进不出（采购入库），分门别类标记货架号 |
| **回收仓** | 书画室旁小仓库 | 可循环利用物资（签字笔、便签纸等） | 从主仓转入，取用时优先从此处拿取 |
| **直接消耗** | 大厅 | 高频消耗品（纸巾等） | 不入回收仓，直接使用消耗 |

### 核心流程

```
采购入库 → 主仓库（记录货架位置）→ 领用出库
                                       ├── 可循环品 → 回收仓 → 优先领用
                                       └── 消耗品 → 直接使用
```

## 当前功能

- **物资分类管理**：固定性物资（耐用品，支持个体追踪）与消耗性物资
- **借出/归还**：支持按数量借还（消耗品）和按个体代号借还（如空调遥控器）
- **遥控器管理**：独立代号管理、搜索过滤、批量添加/删除
- **二维码**：为每个遥控器生成唯一二维码，支持单个/批量打印
- **借用记录**：可折叠查看历史借还记录
- **管理员面板**：密码登录、修改物资总数和低库存阈值

## 工作方向（仅作为后续指引）

### 第一阶段：数据基建与盘点

- [x] **全量盘点入口**：支持按物资、仓库、储位逐项核对，个体扫码及盘盈盘亏修正
- [ ] **标准化数据字段**：品名、位置（仓库/货架号）、数量、计量单位、状态（全新/在库/已领用/已回收/已消耗）
- [ ] **物资清单导出**：支持按仓库、分类导出完整物资清单

### 第二阶段：仓储规划与业务流程

- [ ] **多仓库视图**：主仓库与回收仓分仓展示，支持仓位级定位（仓库 → 货架号 → 具体位置）
- [ ] **主仓入库流程**：采购物资扫码/手动录入 → 指定货架位置 → 入库完成（"只进不出"）
- [ ] **主仓至回收仓转移**：可循环物资从主仓拆封后，转入回收仓，数量同步扣减
- [ ] **领用优先级**：领用时可循环物品优先展示回收仓库存，回收仓不足时再从主仓取用
- [ ] **消耗品标记**：高频消耗品（纸巾等）标记为"直接消耗"，跳过回收仓环节

### 第三阶段：云端部署与智能补货

- [ ] **云端数据库接入**：数据上云，多端（PC / 手机 / 扫码枪终端）实时同步
- [ ] **动态库存预警**：根据物品实际消耗速度自动计算阈值（如按"一个月消耗完毕"动态调整）
- [ ] **汇总报表自动生成**：每半个月或一个月自动生成补货建议报表
- [ ] **邮件通知**：报表通过邮件自动发送给采购负责人

### 第四阶段：硬件集成

- [ ] **无线扫码枪对接**：支持超市通用无线扫码机，取用/归还时扫码即录
- [ ] **扫码操作流程**：扫码 → 自动识别物资 → 确认取用/归还 → 库存实时更新
- [ ] **前台快速终端**：适配扫码枪操作场景的简化界面

## 数据标准

物资信息记录规范，每条记录至少包含：

| 字段 | 说明 | 示例 |
|------|------|------|
| 品名 | 物资名称 | 晨光签字笔 0.5mm 黑色 |
| 仓库 | 所在仓库 | 主仓库 / 回收仓 |
| 位置 | 货架号/具体位置 | A架-3层-2号 |
| 数量 | 当前库存数量 | 50 |
| 计量单位 | 计数单位 | 支 / 箱 / 包 / 个 |
| 分类 | 物资类型 | 固定性物资 / 消耗性物资 |
| 状态 | 当前状态 | 全新 / 已拆封 / 已回收 |

## 技术栈

- Vue 3 (Composition API + `<script setup>`)
- Vite + Vitest
- qrcode
- FastAPI + SQLAlchemy + Alembic
- SQLite / PostgreSQL
- uni-app + Vue 3（微信小程序）
- Docker Compose

## 本地启动

### 后端

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
Set-Location backend
..\.venv\Scripts\uvicorn.exe main:app --reload
```

开发环境可以在 `.env` 中启用 `AUTH_PROVIDER=mock` 和 `MOCK_AUTH_ENABLED=true`。生产环境会强制禁用模拟认证，并要求配置学校认证适配器与 `JWT_SECRET`。

### Web 管理端

```bash
npm install
npm run dev
```

浏览器访问 `http://localhost:5173/`

### 微信小程序

```powershell
Set-Location student-miniapp
npm install
Copy-Item .env.example .env
npm run dev:mp-weixin
```

将生成目录导入微信开发者工具，并在 `student-miniapp/src/manifest.json` 填写真实微信 AppID。生产 API 必须使用 HTTPS 并加入微信合法请求域名。

## 构建

```bash
npm run build
npm run preview
```

```powershell
# 后端测试
.\.venv\Scripts\python.exe -m pytest backend\tests -q

# 管理端测试与构建
npm run test
npm run build

# 微信小程序构建
Set-Location student-miniapp
npm run build:mp-weixin
```

## API 与权限

- 登录：`POST /api/auth/login`、`POST /api/auth/refresh`、`POST /api/auth/logout`
- 当前用户：`GET /api/me`
- 借用申请：`/api/borrow-applications`
- 扫码解析：`POST /api/scan/resolve`
- 审计记录：`GET /api/audit-logs`（仅管理员）
- 所有接口继续使用 `{ "ok": boolean, "data": ..., "msg": string }` 响应结构

角色权限：学生只能管理自己的申请；操作员负责审核和现场确认；管理员额外负责系统设置、用户和审计。

## Git 协作流程

### 前置准备

1. 安装 [Git](https://git-scm.com/downloads)（一路默认即可）
2. 安装 [VS Code](https://code.visualstudio.com/)
3. 注册 [GitHub](https://github.com/) 账号，把用户名发给仓库管理员添加为协作者

### 方式 A：VS Code 直接连接 GitHub（推荐，最简单）

1. 打开 VS Code，点击左侧活动栏的 **源代码管理** 图标（或按 `Ctrl+Shift+G`）
2. 点击 **克隆存储库** → 选择 **从 GitHub 克隆**
3. 首次使用会弹出浏览器让你登录 GitHub 账号，点授权即可
4. 登录后在搜索框输入仓库名 `一站式项目`（或仓库的完整名称），选中后选择本地存放路径
5. 克隆完成后 VS Code 提示"是否打开"，点 **打开** 即可

### 方式 B：命令行克隆

```bash
# 1. 打开终端，cd 到你想要存放的文件夹
cd ~/Desktop

# 2. 克隆仓库（把 <仓库地址> 换成 GitHub 上的实际地址）
git clone <仓库地址>

# 3. 进入项目目录
cd 一站式项目

# 4. 用 VS Code 打开
code .
```

> 如果 `code` 命令不可用：打开 VS Code → `Ctrl+Shift+P` → 输入 `Shell Command: Install 'code' command in PATH` → 回车安装。

### 日常开发流程（从写代码到合并，完整 10 步）

**核心规则：永远不要直接在 main 分支上改代码。**

整个流程分两个阶段：**本地操作**（在你电脑上完成）和 **GitHub 网页操作**（在浏览器完成）。

---

#### 新手必读：分支 vs main，到底有什么区别？

你可以把 Git 仓库想象成一棵树：

```
main 分支（主干）          ← 团队所有已确认的、稳定的代码在这里
│
├── feature/xxx 分支       ← 你从这里分出来，只改你自己的功能
├── fix/xxx 分支           ← 队友从这里分出来，只修他自己的 bug
└── feature/yyy 分支       ← 另一个队友的功能分支
```

- **main 是唯一的真相来源** — 所有人最终合并到这里，它代表"当前线上运行的版本"
- **分支是你的私人工作区** — 你从 main 分出来一条岔路，在这上面随便改，不会影响 main，也不会影响别人的代码
- **PR 就是把你的岔路合并回主干** — 别人 review 确认没问题后，你的代码才真正进入 main

| | 在 main 上直接 commit | 在分支上 commit |
|---|---|---|
| 影响范围 | 立刻影响所有人 | 只影响你自己的分支 |
| 别人能 review 吗？ | 不能，直接生效 | 能，通过 PR |
| 改错了怎么办？ | 很难回退，影响团队 | 删掉分支重来即可 |
| 应该这样做吗？ | **绝对不要** | **这才是正确姿势** |

> 一句话：**你的每一次 commit 都是在分支上进行的，永远不要 commit 到 main。** main 只通过 PR 合并来更新。

**如果你已经在 main 上改了代码怎么办？**

```bash
# 别慌，先不要 commit。执行下面三步：
git stash                    # 把你改的代码暂存起来
git checkout -b feature/xxx  # 创建新分支
git stash pop                # 把代码恢复到新分支上
```

---

#### 阶段一：本地操作（步骤 1-7，在你的电脑/VSCode 里完成）

```bash
# 步骤 1：切换到 main 分支
git checkout main

# 步骤 2：拉取最新代码（确保你和团队进度同步）
git pull origin main

# 步骤 3：从 main 创建你自己的功能分支
# 分支名用英文短横线连接，说清楚你要做什么，比如：
git checkout -b feature/warehouse-view    # 新功能
git checkout -b fix/inventory-count       # 修 bug
git checkout -b docs/update-readme        # 改文档

# 步骤 4：改代码...（在 VSCode 里正常写代码、保存）

# 步骤 5：看看你改了哪些文件（这个步骤只是确认，可以不执行）
git status

# 步骤 6：把所有修改添加到暂存区
git add .

# 步骤 7：提交到本地仓库，写清楚你改了什么
git commit -m "feat: 新增主仓库和回收仓分仓视图"
```

> 到这里为止，你的修改还**只在你自己的电脑上**，GitHub 上什么都没有。

```bash
# 步骤 8：推送到 GitHub（把本地修改上传到云端）
git push origin feature/warehouse-view
```

> 终端会输出一堆信息，看到类似 `remote: Create a pull request...` 的链接就说明推送成功了。

---

#### 阶段二：GitHub 网页操作（步骤 9-10，在浏览器里完成）

> **push 只是把代码传上去了，不等于提交了 PR！** 必须去 GitHub 网页手动创建 PR，仓库管理员才能看到你的改动。

**步骤 9：创建 Pull Request**

1. 打开浏览器，进入你的 GitHub 仓库页面
2. 你会看到页面顶部有一个**黄色的提示条**，写着你的分支名和 **"Compare & pull request"** 绿色按钮 → **直接点它**
3. 如果没看到黄色提示条，手动操作：
   - 点击页面上方的 **Pull requests** 标签
   - 点击绿色的 **New pull request** 按钮
   - `base` 选 **main**（意思是"我要合并到这里"）
   - `compare` 选你的分支（意思是"这是我的改动"）
   - 点击绿色的 **Create pull request**
4. 在标题和描述里写清楚你改了什么、为什么这样改
5. 点击页面下方的 **Create pull request** 提交

**步骤 10：等待 Review 和合并**

1. PR 创建好后，在团队群里发链接，让大家 review
2. 如果有人提了修改建议，你在本地分支继续改 → `git add .` → `git commit` → `git push`，PR 会自动更新
3. 至少一个人点 **Approve** 后，点击 **Merge pull request** → **Confirm merge** 合并到 main
4. 合并完成后，GitHub 会提示 **"Delete branch"**，点一下删掉远程分支，保持仓库整洁

---

#### 一张图总结

```
你的电脑                          GitHub 云端
─────────                        ──────────
git checkout -b xxx    ─→        创建了新分支
写代码改代码...
git add .
git commit -m "xxx"   ─→        提交记录保存在本地
git push               ─→        分支和代码上传到云端
                                 ↓
浏览器打开 GitHub ──→ 点击 "Compare & pull request"  ──→  创建 PR
                                 ↓
                              队友 review → Approve → Merge → 代码进入 main ✅
```

> 这一步很多人会漏：**push 之后一定要去 GitHub 网页手动创建 PR**。不创建 PR，仓库管理员就看不到你的改动，代码永远进不了 main。

### 提交信息规范

```
feat: 新增xxx功能
fix: 修复xxx问题
refactor: 重构xxx模块
docs: 更新文档
style: 样式调整
```

### VS Code 图形化操作（不喜欢命令行的看这里）

VS Code 的源代码管理面板可以完成上述所有操作：

| 操作 | 对应位置 |
|------|---------|
| 拉取最新代码 | 左下角刷新按钮，或 `Ctrl+Shift+P` → `Git: Pull` |
| 创建分支 | 左下角分支名 → 创建新分支 |
| 暂存修改 | 源代码管理面板 → 文件旁边 `+` 号 |
| 提交 | 源代码管理面板 → 输入 message → 点 `✓` |
| 推送 | 左下角同步按钮，或 `Ctrl+Shift+P` → `Git: Push` |
| 发起 PR | GitHub 网页端操作（这一步无法在 VS Code 内完成） |

### 团队协作规则

1. **禁止直接 push 到 main 分支** — main 分支受保护，所有改动必须通过 PR 合并
2. **一个功能一个分支** — 不要在一个分支里混合多个不相关的改动
3. **开发前先拉取** — 每次开始写代码前执行 `git pull origin main`，确保基于最新代码开发
4. **PR 必须有人 review** — 至少一个人看过、确认没问题后才能合并
5. **有冲突先沟通** — 如果 PR 显示有冲突（conflict），先和改动相关的人沟通，一起解决后再合并
6. **不要提交 node_modules** — `.gitignore` 已配置忽略，不要手动把依赖包加进版本库
7. **commit 要小步快跑** — 每做完一个小的功能点就提交一次，不要攒一大堆一起提交

### 遇到问题了？

| 常见问题 | 解决办法 |
|---------|---------|
| `git push` 被拒绝 | 先 `git pull origin main`，解决冲突后再 push |
| 改乱了想回到某个版本 | `git log` 查看历史 → `git checkout <commit-hash>` 临时查看 |
| 在我自己的分支上改错了想重来 | `git checkout .` 丢弃所有本地修改（谨慎！） |
| 分支太多不记得自己在哪里 | `git branch` 查看所有本地分支，当前分支前面有 `*` |
| PR 有冲突 | 在本地 `git checkout main` → `git pull` → `git checkout 你的分支` → `git merge main` → 解决冲突 → `git push` |

## 项目结构

```
backend/
├── routers/                # FastAPI 接口
├── services/               # 库存、申请、邮件和审计服务
├── migrations/             # Alembic 迁移
└── tests/                  # 后端自动化测试
src/
├── api/                    # Web API 客户端
├── components/             # Vue 管理端组件
├── constants/              # 共享状态名称
└── store/                  # 管理端状态
student-miniapp/
└── src/
    ├── pages/              # uni-app 学生端页面
    ├── services/           # 小程序请求与令牌刷新
    └── constants/          # 小程序共享状态名称
```
