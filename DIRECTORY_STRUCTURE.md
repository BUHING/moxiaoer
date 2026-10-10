# GrindBuddy 目录与实现说明

本文以当前工作区为准，说明目录和关键文件的职责、实现状态及功能边界。依赖、缓存、构建产物和机密文件不展开。

## 实现状态

已完成认证、组织、员工与权限纵向模块，以及首页的可用骨架。首页包括受认证和查询权限保护的 Django 聚合 API、OpenAPI 生成的 TypeScript Client、Vue 仪表盘、今日/本周/本月销售指标、上月对比、毛利不可用状态和六项常用功能占位。

`products`、`partners`、`inventory`、`purchases`、`sales` 和 `system` 已建立 app/feature 边界，但暂无可用业务实现。`reports` 已实现首页只读聚合骨架；销售、进货和库存统计仍未实现。六项首页快捷入口会在对应业务模块完成前保持不可用。`warehouses`、`stocktaking`、`transfers` 明确属于首期范围外，只保留边界目录。

```text
grindbuddy/
├── backend/                 # Django REST API
├── frontend/                # Vue 3 单页应用
├── docs/                    # 产品、技术、API、验收与部署规范
├── infra/                   # Nginx 与运维脚本位置
├── .env                     # Docker 运行机私有配置，不提交
├── .env.example             # Docker 运行机配置模板
├── docker-compose.yml       # PostgreSQL、后端、前端容器编排
├── run.py                   # 本机一键启动器
├── README.md                # 项目入口、开发命令与协作规则
├── ENVIRONMENT_BASELINE.md  # 环境及镜像版本基线
└── DIRECTORY_STRUCTURE.md   # 本文档
```

## 根目录文件

| 路径 | 作用与已实现功能 |
| --- | --- |
| `run.py` | 本机一键启动器。使用 `backend/.env` 的本机 PostgreSQL；检查端口、同步依赖、执行迁移并启动 Django 和 Vite；`Ctrl+C` 同时停止。 |
| `README.md` | 项目范围、技术栈、开发命令、规格入口和协作约束。 |
| `DIRECTORY_STRUCTURE.md` | 当前目录、文件职责及实现状态说明。 |
| `ENVIRONMENT_BASELINE.md` | 固定版本：Python `3.14.7`、Node.js `24.19.0`、PostgreSQL `18.6`；说明本机和 Docker 运行机职责。 |
| `docker-compose.yml` | 运行机编排：启动 PostgreSQL、等待健康检查、执行迁移、启动 Gunicorn 和 Nginx。仅 `WEB_PORT`（默认 `8080`）对外开放。 |
| `.env` | Docker 运行机私有变量，包含 Django 密钥和 Docker PostgreSQL 初始密码。部署前需将 `DJANGO_ALLOWED_HOSTS` 加入运行机 IP/DNS；不提交。 |
| `.env.example` | Docker `.env` 安全模板，按“必须修改/通常无需修改/按需修改”标注。 |
| `.python-version` / `.nvmrc` | Python 与 Node.js 的版本锁定。 |
| `.gitignore` / `.dockerignore` | 分别排除 Git 提交和 Docker 构建中的环境文件、依赖、缓存、构建产物和数据库数据。 |
| `.editorconfig` | 文件编码、缩进和换行约定。 |
| `_init_.py` | 根目录 Python 占位文件，不承载业务或启动功能。 |

## 后端：`backend/`

后端使用 Django 6、Django REST Framework、SimpleJWT 和 drf-spectacular。API 根为 `/api/v1/`；开发、测试和生产均使用 PostgreSQL。

| 路径 | 作用与已实现功能 |
| --- | --- |
| `manage.py` | Django 管理入口，用于迁移、检查、运行服务和生成 OpenAPI Schema。 |
| `pyproject.toml` | Python 依赖与 pytest、Ruff、mypy 配置。 |
| `uv.lock` | 精确锁定 Python 依赖；本机和 Docker 均依赖它安装包。 |
| `Dockerfile` | 基于 `python:3.14.7-slim` 的后端镜像，安装锁定依赖并以 Gunicorn 提供服务。 |
| `.env` | 本机原生 PostgreSQL 开发变量；Django 命令和 `run.py` 均会读取，不可与根 Docker `.env` 混用。 |
| `.env.example` | 本机 PostgreSQL 开发配置模板。 |
| `tests/test_health.py` | 跨模块的健康检查 API 测试。 |

### Django 配置：`backend/config/`

| 路径 | 作用 |
| --- | --- |
| `urls.py` | 注册 API 根、健康检查、账号、首页、JWT、OpenAPI Schema 和 Swagger UI。 |
| `asgi.py` / `wsgi.py` | ASGI/WSGI 服务入口；Docker Gunicorn 使用 WSGI。 |
| `settings/base.py` | 共享 app、自定义用户、数据库、JWT、CORS、DRF 与 OpenAPI 配置。 |
| `settings/development.py` | 本机开发设置，开启 `DEBUG`。 |
| `settings/production.py` | Docker 生产设置，关闭 `DEBUG` 并强制要求 Django 密钥。 |
| `settings/test.py` | 测试设置，继承 PostgreSQL 连接并使用快速密码哈希。 |
| `settings/__init__.py` | 默认加载开发设置。 |
| `__init__.py` | Python 包标识。 |

### 通用 API：`backend/apps/common/`

| 路径 | 作用 |
| --- | --- |
| `apps.py` / `__init__.py` | Django app 配置与 Python 包标识。 |
| `urls.py` | `/api/v1/` API 根和 `/api/v1/health/` 健康检查路由。 |
| `views.py` | 匿名 API 名称/版本和健康状态响应，包含 OpenAPI 响应声明。 |
| `exceptions.py` | 统一 DRF 异常处理，将认证、权限和字段错误包装为 `code`、`message`、`errors`、`request_id`。 |
| `migrations/` / `tests/` | 通用基础设施迁移与测试位置，目前无独立实现。 |

### 已实现账号模块：`backend/apps/accounts/`

| 路径 | 作用与已实现功能 |
| --- | --- |
| `apps.py` / `__init__.py` | `accounts` app 注册和 Python 包标识。 |
| `models.py` | UUID 用户、组织、成员关系、权限授予、权限申请、店铺资料。组织是 boss 的租户边界，成员唯一归属组织，权限授予唯一，申请审批状态受数据库约束。 |
| `migrations/0001_initial.py` | 创建账号所有表、UUID 主键、外键、唯一约束和审批状态检查约束。`migrations/__init__.py` 标识迁移包。 |
| `services.py` | 原子注册 boss 并创建组织/成员/店铺，创建 employee，默认/有效权限计算，授权和带行锁的申请审批。 |
| `serializers.py` | 注册、JWT、当前用户、员工、权限申请、店铺资料的 API 序列化器和 Schema 类型。 |
| `views.py` | boss 权限守卫；注册、JWT 包装、当前身份、员工列表/创建/维护、申请提交/批准/拒绝、店铺资料读取/更新。 |
| `urls.py` | `/auth/register/`、`/auth/me/`、`/employees/`、`/permission-requests/`、`/shop-profile/` 路由；JWT 登录/刷新在全局路由中注册。 |
| `tests/test_accounts_api.py` | 注册初始化、错误格式、employee 默认权限、跨组织隔离、审批授权及重复审批拒绝回归测试。`tests/__init__.py` 标识测试包。 |

### 首页聚合：`backend/apps/reports/`

| 路径 | 作用与已实现功能 |
| --- | --- |
| `serializers.py` | 首页时间段指标及响应的 API 序列化器；金额以字符串输出。 |
| `views.py` | `/api/v1/dashboard/` 查询端点，强制认证和 `dashboard.view` 权限；当前无销售单模块时返回零销售额、零单数及不可用毛利。 |
| `urls.py` | 首页 API 路由。 |
| `tests/test_dashboard_api.py` | 未认证拒绝、boss/default employee 查询权限和首页指标响应格式回归测试。 |

### 预留业务 app：`backend/apps/`

每个 app 都有 `__init__.py`、`apps.py`、`migrations/`、`tests/`，但目前没有 models/services/API。`backend/apps/README.md` 规定模块代码和测试的放置方式。

| 目录 | 预期边界 | 状态 |
| --- | --- | --- |
| `products/` | 商品、单位、规格、属性、商品价格。 | 首期计划内，未实现。 |
| `partners/` | 客户、供应商、价格等级。 | 首期计划内，未实现。 |
| `inventory/` | 库存余额、不可变流水及唯一库存写服务。 | 首期计划内，未实现。 |
| `purchases/` | 进货、进货退货草稿及完成动作。 | 首期计划内，未实现。 |
| `sales/` | 销售、销售退货草稿及完成动作。 | 首期计划内，未实现。 |
| `reports/` | 销售、进货、库存统计和首页聚合。 | 已实现首页聚合骨架；三类统计待相关业务单据模块完成后实现。 |
| `system/` | 审计日志和系统配置。 | 预留，未实现。 |
| `warehouses/` | 多仓库。 | 首期范围外。 |
| `stocktaking/` | 盘点。 | 首期范围外。 |
| `transfers/` | 库存调拨。 | 首期范围外。 |

## 前端：`frontend/`

前端使用 Vue 3、TypeScript、Element Plus、Pinia、TanStack Query 和 Vite。开发时 Vite 代理 `/api` 至 Django；Docker 运行机由 Nginx 代理至后端容器。

| 路径 | 作用与已实现功能 |
| --- | --- |
| `package.json` / `package-lock.json` | 前端依赖、`dev`/`build`/`generate:api` 命令和精确锁文件。 |
| `vite.config.ts` | 将 `/api` 代理至 `VITE_DEV_API_ORIGIN` 或本机 `8000`。 |
| `index.html` | Vite SPA HTML 入口。 |
| `Dockerfile` | 用 `node:24.19.0-alpine` 构建静态资源，再部署至 Nginx。 |
| `openapi.json` | 后端生成的 OpenAPI 输入文件，用于离线重新生成 Client。 |
| `.env.example` / `.gitignore` | 可公开的 Vite 变量模板与前端环境/依赖忽略规则。 |
| `tsconfig.json`、`tsconfig.app.json`、`tsconfig.node.json` | TypeScript 项目、应用和 Node 配置。 |
| `README.md` | 前端局部说明。 |
| `public/` | 不经打包直接复制的静态资源，当前含图标。 |
| `.vscode/extensions.json` | 推荐 VS Code 前端开发扩展。 |

### 前端源码：`frontend/src/`

| 路径 | 作用与已实现功能 |
| --- | --- |
| `main.ts` | 创建应用并注册 Pinia、Router、Vue Query、Element Plus。 |
| `App.vue` | 根组件，仅渲染路由。 |
| `router/index.ts` | `/auth` 公共路由、默认 `/dashboard` 首页和 `/settings/employees` 账号工作台路由；未登录重定向、JWT 恢复和失效清除。 |
| `stores/auth.ts` | JWT 本地存储、生成 Client 的 Bearer Token、登录、读取当前用户和退出清理。 |
| `layouts/AppLayout.vue` | 已登录布局，显示组织名与退出操作。 |
| `styles/base.css` | 登录页、首页仪表盘、账号工作台、头部及响应式全局样式。 |
| `style.css` | Vite 初始样式文件，当前未承载业务逻辑。 |
| `assets/` | 图片与 Vite/Vue 初始资源，不承载账号业务逻辑。 |
| `components/HelloWorld.vue` | Vite 初始示例组件，当前未使用。 |
| `views/BootstrapView.vue` | 初始占位视图，已被账号工作台路由替代。 |
| `composables/`、`types/`、`utils/` | 组合逻辑、非 API DTO 共享类型和纯工具函数位置，当前为空。 |
| `tests/` | 前端测试位置，当前未配置测试框架。 |

### API 与认证界面

| 路径 | 作用与已实现功能 |
| --- | --- |
| `src/api/generated/` | 由 `openapi.json` 生成，禁止手改；包含账号和首页模型、请求核心、错误类和 `V1Service`。 |
| `src/api/generated/core/` | Axios 请求执行、取消、错误和 OpenAPI 配置。 |
| `src/api/generated/models/` | 认证、员工、权限申请、店铺、健康检查和首页指标的生成 TypeScript 类型。 |
| `src/api/generated/services/V1Service.ts` | 当前 `/api/v1/` 端点的生成调用方法，包含 `dashboardRetrieve()`；`SchemaService.ts` 为 Schema 调用服务。 |
| `src/api/http/client.ts` | 手写 HTTP 基础设施位置；账号请求当前使用生成 Client。 |
| `src/api/README.md` / `generated/README.md` | API 生成物与手写基础设施分层说明。 |
| `src/features/auth/AuthView.vue` | 登录与 boss 注册。注册成功后自动登录，展示后端字段错误，并明确 employee 不可自助注册。 |
| `src/features/auth/AccountWorkspace.vue` | 账号工作台：boss 可建员工和批准/拒绝申请；employee 可看权限和提交申请。 |
| `src/features/reports/DashboardView.vue` | 默认首页：通过生成 Client 查询今日/本周/本月销售指标和上月对比；毛利成本口径未确认时显示不可用，六项快捷入口在相关模块完成前禁用。 |
| `src/features/README.md` | Vue feature 的组织规则。 |
| `src/features/products/`、`partners/`、`inventory/`、`purchases/`、`sales/`、`system/` | 首期计划模块前端边界，当前为空。 |
| `src/features/warehouses/`、`stocktaking/`、`transfers/` | 范围外模块前端边界，当前为空。 |

## 文档：`docs/`

| 文件或目录 | 作用 |
| --- | --- |
| `功能模块设计.docx` | 上游功能主设计，定义模块范围、角色和交互参考。 |
| `requirements.md` | 可实现需求范围、流程和待确认事项。 |
| `domain-rules.md` | 库存、单据、金额、权限、并发、审计不变量。 |
| `data-model.md` | 逻辑实体、关系、索引、约束及敏感/派生数据规则。 |
| `api.md` | `/api/v1/`、响应/错误格式、端点、权限与兼容约定。 |
| `ui.md` | 页面、路由、权限入口和交互状态规范。 |
| `acceptance.md` | 后端/前端验收场景、优先级和回归范围。 |
| `system-design.md` | 技术架构、模块边界、逻辑表和 PostgreSQL 参考设计。 |
| `deployment.md` | Docker 运行机 `.env`、部署、验证、升级、备份和故障排查步骤。 |
| `skills/` | AI 协作提示词。`00-使用顺序.md` 指定顺序；`01` 至 `07` 分别生成规格；`08-模块开发提示词模板.md` 执行纵向模块；`09` 初始化项目；`10` 生成系统设计。 |

## 基础设施：`infra/`

| 路径 | 作用 |
| --- | --- |
| `nginx/default.conf` | Docker 前端容器的 Nginx：Vue SPA 回退，并将 `/api/` 转发到内部 `backend:8000`。 |
| `scripts/README.md` | 备份、恢复、初始化等可审查运维脚本的放置规则。 |
| `scripts/` | 未来运维脚本目录，当前无可执行脚本。 |

## 维护规则

1. 开发新模块前，先确认 `docs/` 的范围与领域规则，再在对应 Django app 和 `frontend/src/features/` 完成可验收的完整链路。
2. 修改后端模型必须新增 migration；修改 API 后必须重新生成 `frontend/openapi.json` 及 `src/api/generated/`，不得手写重复 DTO。
3. 库存、单据、金额、权限和审计由后端服务层裁决；前端只处理交互与反馈。
4. 新增、删除或移动关键文件时同步更新本文；环境、镜像或部署方式变化时同步更新 `ENVIRONMENT_BASELINE.md` 与 `docs/deployment.md`。