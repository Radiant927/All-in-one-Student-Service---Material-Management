# 团队开发约定

## 分支与提交

- 禁止直接提交或推送到 `main`，一个功能使用一个分支和一个可审阅的 PR。
- 分支使用 `feature/xxx`、`fix/xxx`、`docs/xxx`。
- 提交使用 `feat:`、`fix:`、`refactor:`、`docs:`、`style:`。
- 数据库结构变化必须附带 Alembic 迁移，不能只修改 `models.py`。
- API 行为变化必须附带 pytest；共享前端状态或转换函数必须附带 Vitest。

## 命名

- Python、数据库字段和表名：`snake_case`，表名使用复数。
- Python 类和 Vue 组件：`PascalCase`。
- JavaScript 变量和函数：`camelCase`。
- API 路径：小写复数名词；状态变化使用清晰的操作动词。
- 接口响应统一为 `{ ok, data, msg }`。
- 业务术语固定为：`material`（物资）、`warehouse`（仓库）、`storage_location`（储位）、`BorrowApplication`（借用申请）。
- 库存动作继续使用 `inbound`、`transfer`、`borrow`、`return`，领取不新增第二种库存动作。
- 借用申请状态只从后端 `constants.py`、Web `applicationStatus.js` 和小程序同名常量文件引用。

## 合并前检查

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm run test
npm run build
Set-Location student-miniapp
npm run build:mp-weixin
```

PR 描述至少包含：变更目的、接口或迁移影响、验证结果、回滚方式。涉及学校统一认证、微信 AppID、域名或生产密钥时，只提交配置字段说明，不提交真实凭据。

