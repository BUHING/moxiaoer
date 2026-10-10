# GrindBuddy 进销存系统

面向小型零售或批发团队的进销存 Web 系统，采用 Vue 3 前端和 Django REST API 后端。当前代码包含账号与权限、商品与基础资料、客户与供应商、采购与销售及退货、库存查询、统计报表、店铺资料和标签打印模块。

项目提供本机开发启动入口和 Docker Compose 部署配置，数据库使用 PostgreSQL。本文以实际源码、路由和配置为准；仅有占位目录的能力不列为已实现功能。

## 目录结构

以下展开实际业务目录和主要文件。各后端模块的迁移版本、Python 包标识文件，以及 OpenAPI 自动生成的逐个类型文件不重复列出；依赖、缓存和构建产物不展开。本地环境文件仅说明用途，不展示真实配置。

```text
grindbuddy/
├── README.md                        # 项目介绍、目录说明、启动与维护入口
├── DIRECTORY_STRUCTURE.md           # 独立目录说明，部分实现状态描述早于当前代码
├── ENVIRONMENT_BASELINE.md          # 开发工具、基础镜像版本和环境移植基线
├── run.py                           # 本机启动器：检查端口、安装依赖、迁移并启动前后端
├── _init_.py                        # 根目录 Python 占位文件，不是启动入口
├── docker-compose.yml               # PostgreSQL、Gunicorn 后端和 Nginx 前端容器编排
├── .env                             # Docker 部署私有配置，不提交
├── .env.example                     # Docker 配置模板，含数据库、邮件和访问端口设置
├── .python-version                  # Python 版本约定
├── .nvmrc                           # Node.js 版本约定
├── .editorconfig                    # 编码、缩进、换行和文件末尾约定
├── .gitignore                       # 排除环境文件、依赖、缓存、构建及备份产物
├── .dockerignore                    # 排除根构建上下文中的机密和无关产物
├── backend/                         # Django REST API 与后端测试
│   ├── manage.py                    # Django 管理入口：迁移、检查、开发服务、Schema 生成
│   ├── pyproject.toml               # Python 依赖及 pytest、Ruff、mypy 配置
│   ├── uv.lock                      # Python 依赖锁文件
│   ├── Dockerfile                   # Python + uv 后端镜像，以 Gunicorn 提供服务
│   ├── .dockerignore                # 后端构建过滤，避免本机虚拟环境进入容器
│   ├── .env.example                 # 本机 PostgreSQL 开发配置模板
│   ├── test.sqlite3                 # 本地 SQLite 文件；开发和生产默认不使用
│   ├── config/                      # Django 项目配置
│   │   ├── urls.py                  # 注册业务 API、JWT 登录刷新、OpenAPI 与 Swagger UI
│   │   ├── asgi.py                  # ASGI 服务入口
│   │   ├── wsgi.py                  # WSGI 服务入口，供 Gunicorn 使用
│   │   └── settings/
│   │       ├── __init__.py          # 默认导入开发配置
│   │       ├── base.py              # 读取后端 .env，配置数据库、认证、邮件、CORS 和 DRF
│   │       ├── development.py       # 开发设置，开启 DEBUG
│   │       ├── production.py        # 生产设置，关闭 DEBUG 并要求提供密钥
│   │       └── test.py              # 测试设置；快速密码哈希，可选 SQLite 测试数据库
│   ├── apps/                        # 按业务域拆分的 Django app
│   │   ├── README.md                # 后端模块与测试代码放置规范
│   │   ├── accounts/                # 用户、组织、员工、权限和店铺资料
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 用户、组织成员、权限授予/申请和店铺模型
│   │   │   ├── services.py          # 老板注册初始化、员工创建、授权和权限审批
│   │   │   ├── serializers.py       # 账号请求校验、响应序列化和 API 类型声明
│   │   │   ├── views.py             # 注册登录、密码重置、员工、权限和店铺接口
│   │   │   ├── urls.py              # 账号业务路由，JWT 登录/刷新另由全局路由注册
│   │   │   ├── migrations/          # 账号结构及超级用户限制等历史迁移
│   │   │   └── tests/
│   │   │       └── test_accounts_api.py # 注册、员工权限、审批和组织隔离回归
│   │   ├── common/                  # 通用 API 基础设施
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── exceptions.py        # 统一 API 异常格式
│   │   │   ├── views.py             # 匿名 API 根信息与健康检查
│   │   │   ├── urls.py              # API 根和 health 路由
│   │   │   ├── migrations/          # 迁移包，目前仅包标识
│   │   │   └── tests/               # 模块测试包，目前仅包标识
│   │   ├── products/                # 商品、单位、规格、属性和分级价格
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 商品、规格/属性定义与取值、商品价格模型
│   │   │   ├── services.py          # 初始化基础资料、维护商品、创建初始库存与流水
│   │   │   ├── serializers.py       # 商品及基础资料的请求校验和响应结构
│   │   │   ├── views.py             # 商品、单位、规格、属性、选项与价格等级接口
│   │   │   ├── urls.py              # 商品及基础资料路由
│   │   │   ├── migrations/          # 商品、采购价、备注、规格和供应商等迁移
│   │   │   └── tests/
│   │   │       └── test_products.py  # 商品创建、初始库存、基础资料与隔离回归
│   │   ├── partners/                # 客户、供应商与价格等级数据
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 客户、供应商和价格等级模型
│   │   │   ├── serializers.py       # 客户与供应商的字段校验和响应序列化
│   │   │   ├── views.py             # 客户/供应商增改查、停用和删除限制
│   │   │   ├── urls.py              # 客户与供应商路由
│   │   │   ├── migrations/          # 往来单位及联系信息迁移
│   │   │   └── tests/
│   │   │       ├── test_customers_api.py # 客户接口与组织隔离回归
│   │   │       └── test_suppliers_api.py # 供应商接口与组织隔离回归
│   │   ├── inventory/               # 库存余额、库存流水和幂等记录
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # StockBalance、StockMovement、IdempotencyRecord
│   │   │   ├── serializers.py       # 库存余额和流水响应序列化
│   │   │   ├── views.py             # 受权限保护的只读库存查询与分页
│   │   │   ├── urls.py              # 库存余额与流水路由
│   │   │   ├── migrations/          # 库存表、关联关系和幂等表迁移
│   │   │   └── tests/
│   │   │       └── test_inventory_api.py # 库存查询、权限和组织隔离回归
│   │   ├── purchases/               # 采购单与采购退货单
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 采购/退货单头、明细与来源关联
│   │   │   ├── services.py          # 草稿、完成、退货校验、库存事务、幂等和删除反向
│   │   │   ├── serializers.py       # 单据和明细的请求校验与响应结构
│   │   │   ├── views.py             # 采购/退货列表、详情、编辑、完成和删除接口
│   │   │   ├── urls.py              # 采购与采购退货路由
│   │   │   ├── migrations/          # 单据、备注和可选供应商/来源采购单迁移
│   │   │   └── tests/
│   │   │       └── test_purchases_api.py # 采购入库、退货、幂等和删除限制回归
│   │   ├── sales/                   # 销售单与销售退货单
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 销售/退货单头、明细、成本快照和来源关联
│   │   │   ├── services.py          # 草稿、出库、退货、成本快照、幂等和删除反向
│   │   │   ├── serializers.py       # 销售/退货请求校验与响应结构
│   │   │   ├── views.py             # 销售/退货列表、详情、编辑、完成和删除接口
│   │   │   ├── urls.py              # 销售单与销售退货路由
│   │   │   ├── migrations/          # 单据、成本快照、来源销售单和可选客户迁移
│   │   │   └── tests/
│   │   │       └── test_sales_api.py # 出库、退货、库存不足、成本和幂等回归
│   │   ├── reports/                 # 首页指标和销售、采购、库存报表
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── services.py          # 聚合销售净额/成本/毛利、采购净额和库存价值
│   │   │   ├── serializers.py       # 仪表盘与三类报表响应结构
│   │   │   ├── views.py             # 权限、日期范围校验和统计接口
│   │   │   ├── urls.py              # dashboard 与 reports 路由
│   │   │   ├── migrations/          # 迁移包，无独立报表模型
│   │   │   └── tests/
│   │   │       └── test_dashboard_api.py # 首页、报表、成本与权限回归
│   │   ├── system/                  # 标签打印模板管理
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 标签模板、尺寸、方向和 JSON 内容
│   │   │   ├── serializers.py       # 标签模板参数校验与响应结构
│   │   │   ├── views.py             # 标签模板查询、创建和详情维护接口
│   │   │   ├── urls.py              # label-templates 路由
│   │   │   ├── migrations/          # 标签模板表迁移
│   │   │   └── tests/               # 模块测试包，目前仅包标识
│   │   ├── warehouses/              # 仓库基础模型与服务，尚无独立管理 API/页面
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── models.py            # 组织仓库、默认仓库标记和唯一约束
│   │   │   ├── services.py          # 确保默认仓库存在、查找组织内有效仓库
│   │   │   ├── migrations/          # 仓库结构和默认仓库初始化迁移
│   │   │   └── tests/               # 模块测试包，目前仅包标识
│   │   ├── stocktaking/             # 盘点占位，尚无业务实现
│   │   │   ├── apps.py              # Django app 注册配置
│   │   │   ├── migrations/          # 迁移包，目前仅包标识
│   │   │   └── tests/               # 测试包，目前仅包标识
│   │   └── transfers/               # 调拨占位，尚无业务实现
│   │       ├── apps.py              # Django app 注册配置
│   │       ├── migrations/          # 迁移包，目前仅包标识
│   │       └── tests/               # 测试包，目前仅包标识
│   └── tests/
│       └── test_health.py           # API 根与健康检查回归测试
├── frontend/                        # Vue 3 + TypeScript 单页应用
│   ├── README.md                    # 前端局部说明
│   ├── package.json                 # 前端依赖及 dev/build/preview/generate:api 脚本
│   ├── package-lock.json            # npm 依赖锁文件
│   ├── index.html                   # Vite HTML 入口与页面元信息
│   ├── vite.config.ts               # Vue 插件和开发环境 /api 代理
│   ├── tsconfig.json                # TypeScript 项目引用入口
│   ├── tsconfig.app.json            # Vue 应用 TypeScript 配置
│   ├── tsconfig.node.json           # Vite 等 Node 工具的 TypeScript 配置
│   ├── openapi.json                 # 后端 OpenAPI Schema 快照
│   ├── Dockerfile                   # Node 构建静态页面，Nginx 提供页面及 API 代理
│   ├── .env.example                 # 前端 API 地址和开发代理目标模板
│   ├── .gitignore                   # 前端环境、依赖和构建产物忽略规则
│   ├── .vscode/
│   │   └── extensions.json          # 推荐编辑器扩展
│   ├── public/                      # 原样复制的公共静态资源
│   │   ├── favicon.svg              # 网站图标
│   │   └── icons.svg                # 页面使用的 SVG 图标资源
│   ├── src/
│   │   ├── main.ts                  # 注册 Pinia、路由、Vue Query、Element Plus 与 API 配置
│   │   ├── App.vue                  # 根组件，渲染当前路由
│   │   ├── style.css                # 保留的 Vite 初始样式
│   │   ├── api/                     # HTTP 基础设施、业务辅助请求与生成 Client
│   │   │   ├── README.md            # 手写 API 基础设施与生成代码的分层规范
│   │   │   ├── configure.ts         # 生成 Client 地址、Token 注入和刷新处理
│   │   │   ├── account.ts           # 密码重置和单据删除辅助请求
│   │   │   ├── pagination.ts        # 分页响应类型与遍历全部页的辅助方法
│   │   │   ├── http/
│   │   │   │   └── client.ts        # Axios 基础实例
│   │   │   └── generated/           # OpenAPI 生成代码，不手工修改
│   │   │       ├── README.md        # API 生成物使用约定
│   │   │       ├── index.ts         # 生成类型、请求核心和服务的统一导出
│   │   │       ├── core/            # 请求执行、取消、错误、响应类型与 OpenAPI 配置
│   │   │       ├── models/          # 账号、商品、单据、库存、报表等生成 TypeScript 类型
│   │   │       └── services/
│   │   │           ├── V1Service.ts # /api/v1/ 业务接口调用方法
│   │   │           └── SchemaService.ts # OpenAPI Schema 接口调用方法
│   │   ├── assets/                  # 参与构建的图片和保留的脚手架资源
│   │   │   ├── hero.png             # 页面图片资源
│   │   │   ├── vue.svg              # Vue 初始图标资源
│   │   │   └── vite.svg             # Vite 初始图标资源
│   │   ├── components/
│   │   │   └── HelloWorld.vue       # 保留的 Vite 示例组件，未接入业务路由
│   │   ├── composables/             # 共享组合式逻辑预留目录，当前为空
│   │   ├── features/                # 按业务域组织的页面
│   │   │   ├── README.md            # 前端 feature 分层与命名规范
│   │   │   ├── auth/
│   │   │   │   ├── AuthView.vue     # 登录、老板注册和找回密码入口
│   │   │   │   ├── PasswordResetView.vue # 重置链接页面与新密码提交
│   │   │   │   └── AccountWorkspace.vue # 员工、权限申请/审批与店铺资料工作台
│   │   │   ├── products/
│   │   │   │   └── ProductWorkspace.vue # 商品列表、编辑和单位/规格/属性维护
│   │   │   ├── partners/
│   │   │   │   ├── PartnerWorkspace.vue # 客户与价格等级页面
│   │   │   │   └── SupplierWorkspace.vue # 供应商页面
│   │   │   ├── purchases/
│   │   │   │   └── PurchaseWorkspace.vue # 采购与采购退货共用工作台
│   │   │   ├── sales/
│   │   │   │   └── SalesWorkspace.vue # 销售与销售退货共用工作台
│   │   │   ├── inventory/
│   │   │   │   └── InventoryWorkspace.vue # 库存余额与库存流水共用查询页
│   │   │   ├── reports/
│   │   │   │   ├── DashboardView.vue # 首页销售指标、上月对比和快捷业务入口
│   │   │   │   └── ReportWorkspace.vue # 销售、采购和库存统计页面
│   │   │   ├── system/
│   │   │   │   └── LabelPrintWorkspace.vue # 导入/保存模板、预览和浏览器打印
│   │   │   ├── warehouses/          # 仓库页面预留，当前为空
│   │   │   ├── stocktaking/         # 盘点页面预留，当前为空
│   │   │   └── transfers/           # 调拨页面预留，当前为空
│   │   ├── layouts/
│   │   │   └── AppLayout.vue        # 登录后布局、导航和退出操作
│   │   ├── router/
│   │   │   └── index.ts             # 页面路由、默认首页与登录状态守卫
│   │   ├── stores/
│   │   │   └── auth.ts              # JWT 存储、登录、当前用户和退出状态
│   │   ├── styles/
│   │   │   └── base.css             # 全局业务样式与响应式布局
│   │   ├── types/                   # 非 API 共享类型预留目录，当前为空
│   │   ├── utils/
│   │   │   └── numberFormat.ts      # 数量与价格的中文显示格式化
│   │   └── views/
│   │       └── BootstrapView.vue    # 保留的初始化视图，未接入当前路由
│   └── tests/                       # 前端测试预留目录，尚未配置测试框架或脚本
├── docs/                            # 需求、领域、设计、接口、界面和验收资料
│   ├── project-introduction.md      # 项目介绍资料
│   ├── requirements.md              # 需求范围、角色、流程和非功能要求
│   ├── domain-rules.md              # 库存、单据、金额、权限和并发约束
│   ├── data-model.md                # 业务实体、关系、字段、约束和索引设计
│   ├── api.md                       # API 路径、数据结构、权限和错误契约
│   ├── ui.md                        # 导航、页面、表单和交互状态规格
│   ├── acceptance.md                # 验收用例、优先级和回归范围
│   ├── system-design.md             # 系统架构、模块边界与设计基线
│   ├── deployment.md                # Docker 部署、升级、备份和故障排查
│   ├── 功能模块设计.docx             # 上游功能模块设计资料
│   └── skills/                      # 文档生成与模块开发提示词，不是运行时代码
│       ├── 00-使用顺序.md             # 提示词使用流程
│       ├── 01-生成需求规格提示词.md     # 需求规格生成
│       ├── 02-生成领域规则提示词.md     # 领域规则生成
│       ├── 03-生成数据模型提示词.md     # 数据模型生成
│       ├── 04-生成API规范提示词.md      # API 契约生成
│       ├── 05-生成界面规格提示词.md     # 界面规格生成
│       ├── 06-生成验收测试提示词.md     # 验收用例生成
│       ├── 07-生成项目README提示词.md   # 项目 README 生成
│       ├── 08-模块开发提示词模板.md     # 业务模块开发任务模板
│       ├── 09-初始化项目与目录说明提示词.md # 项目初始化与目录说明生成
│       └── 10-生成系统设计说明书提示词.md # 系统设计文档生成
├── infra/                           # 部署基础设施
│   ├── nginx/
│   │   └── default.conf             # Vue SPA 路由回退，将 /api/ 代理至 backend:8000
│   └── scripts/
│       └── README.md                # 运维脚本放置规范，目前没有可执行脚本
└── backups/                         # 本地备份存放目录，备份产物不提交
```

后端各 app、迁移包与测试包中的 `__init__.py` 用于 Python 包标识；`apps.py` 用于 Django 注册。库存写入逻辑实际位于商品、采购和销售服务中，库存模块自身只提供查询接口。价格等级模型位于往来单位模块，管理接口由商品模块提供。

## 当前功能

| 模块 | 当前代码包含的能力 |
| --- | --- |
| 账号与权限 | 老板注册并创建组织、JWT 登录/刷新、邮件密码重置、员工管理、权限申请与审批、店铺资料；业务数据按组织隔离。 |
| 商品与基础资料 | 商品及初始库存、采购价、供应商关联、单位、规格、属性及选项、价格等级和商品分级价格。 |
| 客户与供应商 | 客户/供应商查询、创建、修改、停用，以及被引用资料的删除限制。 |
| 采购 | 采购单和采购退货单草稿、完成、查询及删除；完成时联动库存与流水。 |
| 销售 | 销售单和销售退货单草稿、完成、查询及删除；库存不足校验、来源销售明细退货数量校验和成本快照。 |
| 库存 | 库存余额与流水的只读查询、筛选和分页。 |
| 统计 | 首页销售指标与上月对比；销售、采购、库存报表，包含净额、成本和毛利等聚合。 |
| 标签打印 | JSON 标签模板保存与维护、商品字段预览、份数选择和浏览器打印；条码元素目前是文本展示，不是可扫描条码编码。 |

仓库目录已有模型、默认仓库服务和迁移，但尚无独立仓库管理接口或页面。盘点、调拨仅保留 app 和前端目录，不能作为可用功能。

## 技术栈

| 部分 | 技术与配置 |
| --- | --- |
| 后端 | Python、uv、Django 6、Django REST Framework、SimpleJWT、drf-spectacular、psycopg、Gunicorn。 |
| 前端 | Vue 3、TypeScript、Vite、Vue Router、Element Plus、Pinia、Axios、TanStack Query for Vue。 |
| 数据库 | 开发/生产默认 PostgreSQL；测试配置支持显式切换 SQLite。 |
| API 类型 | openapi-typescript-codegen 根据 OpenAPI 生成 TypeScript 类型与 Axios Client。 |
| 后端验证 | pytest、pytest-django、Ruff；另有 mypy 与 django-stubs 配置。 |
| 部署 | Docker Compose 编排数据库、后端和前端；Nginx 托管静态资源并反向代理 API。 |

环境基线为 Python `3.14.7`、uv `0.12.7`、Node.js `24.19.0`、npm `11.17.0`、PostgreSQL `18.6`。Docker 使用固定标签 `python:3.14.7-slim`、`node:24.19.0-alpine`、`postgres:18.6` 和 `nginx:1.27.5-alpine`。版本与移植规则见 [ENVIRONMENT_BASELINE.md](ENVIRONMENT_BASELINE.md)。

## 快速开始

### 本机开发

1. 安装与环境基线一致的 Python、uv、Node.js、npm 和 PostgreSQL。本机开发不依赖 Docker。
2. 在 PostgreSQL 中创建应用角色和数据库，名称需与后端环境配置一致；模板默认角色为 `grindbuddy_app`，数据库为 `grindbuddy`。
3. 首次配置时，从 [后端配置模板](backend/.env.example) 创建后端本地环境文件，从 [前端配置模板](frontend/.env.example) 创建前端本地环境文件。已有配置不要覆盖。

Linux 下首次复制模板，在项目根目录执行：

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Windows PowerShell 中对应使用 `Copy-Item backend/.env.example backend/.env` 和 `Copy-Item frontend/.env.example frontend/.env`。

4. 填写本机数据库连接信息，并替换 `DJANGO_SECRET_KEY` 和 `DATABASE_PASSWORD` 的占位值。
5. 在项目根目录运行启动器：

```bash
python run.py
```

Linux 中若命令名为 `python3`，使用 `python3 run.py`。启动器会读取后端和前端本地环境文件、检查端口、执行 `uv sync` 与 `npm install`、运行 Django 迁移，再启动两个开发服务。

默认访问 `http://127.0.0.1:5173/`。首次使用从登录页注册老板账号，员工由老板创建；不使用 Django 超级用户作为业务入口。按 `Ctrl+C` 停止前后端服务。

### Docker 部署

运行机需要 Docker Engine 和 Docker Compose 插件，不需要在宿主机安装应用的 Python、Node.js 或 PostgreSQL。

首次从 [根配置模板](.env.example) 创建根目录本地环境文件，至少替换 Django 密钥、数据库密码和允许访问的主机；需要密码找回时填写真实 SMTP 配置与重置页面地址。已有配置不要覆盖。

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Windows PowerShell 中复制模板使用 `Copy-Item .env.example .env`。Compose 等待数据库健康检查后执行迁移，默认通过 `http://127.0.0.1:8080/` 访问。远程访问使用 `http://<运行机IP>:<WEB_PORT>/`，并相应配置 `DJANGO_ALLOWED_HOSTS` 与防火墙。

数据库和后端端口仅在容器网络内使用；PostgreSQL 数据保存在 `postgres_data` 命名卷。完整步骤见 [docs/deployment.md](docs/deployment.md)。

## 运行方式

以下命令除特别说明外均在项目根目录执行。Windows PowerShell 若限制 `npm.ps1`，将 `npm` 换成 `npm.cmd`。

### 根目录启动器

| 命令 | 说明 |
| --- | --- |
| `python run.py` | 安装依赖、执行迁移，启动默认后端 `8000` 和前端 `5173`。 |
| `python run.py --backend-port 8001 --frontend-port 5174` | 指定前后端端口，并自动调整启动器使用的 API 代理目标。 |
| `python run.py --host 0.0.0.0` | 开发服务监听所有网卡；局域网访问还需配置允许主机并放行端口。 |
| `python run.py --help` | 查看启动参数。 |

端口被占用时启动器会报错退出，不会自动停止已有服务。

### 分别启动前后端

后端：

```bash
uv --directory backend sync
uv --directory backend run python manage.py migrate
uv --directory backend run python manage.py runserver
```

在另一个终端启动前端：

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

分别启动时，前端通过 `VITE_API_BASE_URL` 调用 API；相对路径 `/api/v1` 可使用 Vite 代理，代理目标由 `VITE_DEV_API_ORIGIN` 指定。根启动器会覆盖这两个变量，使用相对 API 路径并指向本次后端端口。

### 构建与验证

```bash
uv --directory backend run python manage.py check
uv --directory backend run pytest
uv --directory backend run ruff check .
npm --prefix frontend run build
```

后端 pytest 自动使用测试配置，默认连接 PostgreSQL。执行测试的数据库角色需要创建测试数据库的权限。只验证某个模块时，可指定后端相对路径：

```bash
uv --directory backend run pytest apps/sales/tests -q
```

设置环境变量 `USE_SQLITE_TEST_DB=1` 可切换为 SQLite 测试数据库；它不能替代 PostgreSQL 的行锁和并发验证。前端目前没有测试脚本，`build` 执行 Vue/TypeScript 类型检查和 Vite 构建。

```bash
npm --prefix frontend run preview
```

`preview` 用于预览已有前端构建，不启动后端，也不等同于完整部署；API 地址在前端构建时确定。

### Docker 日常命令

| 命令 | 说明 |
| --- | --- |
| `docker compose up --build -d` | 构建或升级服务并在后台启动。 |
| `docker compose up -d` | 启动已有镜像。 |
| `docker compose ps` | 查看三个服务的运行状态。 |
| `docker compose logs -f` | 跟踪服务日志。 |
| `docker compose down` | 停止并移除容器，保留数据库命名卷。 |

不要使用 `docker compose down -v` 清理正在使用的部署，它会删除数据库命名卷。数据库逻辑备份与升级步骤见 [docs/deployment.md](docs/deployment.md)；当前没有应用内备份恢复接口或可执行运维脚本。

## 环境变量

根目录本地环境文件供 Compose 使用；后端本地环境文件供原生 Django 和启动器使用；前端本地环境文件供 Vite 和启动器使用。不要混用开发数据库和容器数据库配置。已有进程环境变量优先于后端/启动器加载的本地配置。

| 变量 | 用途与当前配置 |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | Django 配置模块；启动器固定使用开发配置，Compose 固定使用生产配置，pytest 默认使用测试配置。 |
| `DJANGO_SECRET_KEY` | Django 密钥；生产配置要求提供，不能使用模板占位值。JWT 当前沿用 SimpleJWT 默认签名配置。 |
| `DJANGO_DEBUG` | 基础配置的调试开关；开发配置强制开启，生产配置强制关闭。 |
| `DJANGO_ALLOWED_HOSTS` | 后端允许的主机名/IP，英文逗号分隔；远程访问需加入实际主机。 |
| `DATABASE_HOST` / `DATABASE_PORT` | PostgreSQL 地址；本机模板为 `127.0.0.1:5432`，Compose 注入 `db:5432`。 |
| `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` | 数据库名、角色与密码；本机开发需预先创建，Docker 首次初始化时创建。 |
| `CORS_ALLOWED_ORIGINS` | 允许跨域的完整来源列表；直接跨域访问 API 时需与浏览器来源一致。 |
| `VITE_API_BASE_URL` | 前端业务 API 地址；模板为 `http://127.0.0.1:8000/api/v1`，Docker 构建使用 `/api/v1`。 |
| `VITE_DEV_API_ORIGIN` | Vite 开发代理目标，默认 `http://127.0.0.1:8000`。 |
| `WEB_PORT` | Docker 对外 HTTP 端口，默认 `8080`。 |
| `PASSWORD_RESET_URL` | 密码重置邮件的前端链接，必须包含 `{uid}` 和 `{token}` 占位符。 |
| `DEFAULT_FROM_EMAIL` | 密码重置邮件的发件地址。 |
| `EMAIL_BACKEND` | 邮件后端，源码默认控制台输出；真实邮件需配置 SMTP 后端。 |
| `EMAIL_HOST` / `EMAIL_PORT` | SMTP 主机与端口；源码默认端口 `587`。 |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | SMTP 凭据和 TLS 开关，TLS 默认开启。 |
| `USE_SQLITE_TEST_DB` | 仅测试配置读取；设置为 `1` 时使用 SQLite。 |

开发时可将邮件变量补充到后端本地环境文件；默认控制台邮件不会真正投递。Docker 根模板中的 SMTP 示例也必须替换为可用配置。JWT 访问令牌当前有效期为 30 分钟，刷新令牌为 1 天，由后端设置定义，没有额外的 JWT 有效期环境变量。

本地环境文件、数据库密码、SMTP 密码、Token 和业务备份不得提交；`VITE_*` 会进入前端构建，不能存放后端密钥或数据库凭据。

## API 与类型同步

| 地址 | 用途 |
| --- | --- |
| `/api/v1/` | API 根信息。 |
| `/api/v1/health/` | 匿名健康检查。 |
| `/api/v1/auth/token/` | JWT 登录。 |
| `/api/v1/auth/token/refresh/` | 刷新访问令牌。 |
| `/api/schema/` | drf-spectacular 生成的 OpenAPI Schema。 |
| `/api/docs/` | Swagger UI 交互式 API 文档。 |

开发环境在 `http://127.0.0.1:8000` 下访问这些地址；Docker 部署通过前端对外端口访问同一路径。业务 API 使用 Bearer Token，权限由后端校验。

后端在默认 `8000` 端口启动后，生成前端 Client：

```bash
npm --prefix frontend run generate:api
```

该脚本读取 `http://127.0.0.1:8000/api/schema/`，输出到前端生成目录；它不会自动更新本地 Schema 快照。接口变更时另行同步快照：

```bash
uv --directory backend run python manage.py spectacular --file ../frontend/openapi.json --format openapi-json
```

如果后端使用其他端口，生成时需调整 Schema 输入地址。不要手工修改 [生成 Client](frontend/src/api/generated/index.ts) 或复制后端 DTO；手写 HTTP 配置和辅助逻辑放在生成目录之外。

## 维护规范

- 后端代码按业务域放入对应 app；模型、请求校验、领域服务和视图分别放置，模块测试留在同域测试目录。pytest 收集规则配置在 [backend/pyproject.toml](backend/pyproject.toml)。
- 前端业务页面放在对应 feature，路由、状态、公共样式和工具分别集中管理；API 类型优先复用生成结果。
- 改动数据库结构需新增 Django migration；改动 API 需同步 Schema、生成 Client 和相关测试。
- 商品初始库存、采购、销售和退货通过后端受控服务变更库存；余额与流水一起更新，普通库存 API 只读。
- 数量和金额使用后端 `Decimal` 与数据库十进制字段；API 的数量、金额以字符串表达，前端格式化仅用于展示。
- 单据完成动作需要 `Idempotency-Key`；草稿可编辑，已完成单据不可编辑。删除已完成单据时反向库存并清理相应流水、幂等记录；有关联退货单、流水不完整或反向后库存不足时拒绝删除。
- 当前销售成本使用完成时的商品采购价快照；销售退货沿用原销售明细成本快照，库存报表按当前商品采购价计算价值，不应表述为财务总账或完整成本核算。
- 后端校验组织隔离和功能权限，不能以隐藏前端按钮代替接口授权。
- 需求、规则、字段和接口变化时同步相关规格与验收文档；不要将未接入的占位目录或设计目标描述为已实现能力。

## 项目文档

| 文档 | 作用 |
| --- | --- |
| [docs/project-introduction.md](docs/project-introduction.md) | 项目介绍资料。 |
| [docs/requirements.md](docs/requirements.md) | 产品范围、角色、流程与非功能需求。 |
| [docs/domain-rules.md](docs/domain-rules.md) | 库存、单据、金额、权限与并发约束。 |
| [docs/data-model.md](docs/data-model.md) | 数据实体、关系、约束和索引设计。 |
| [docs/api.md](docs/api.md) | API 契约、动作端点和错误格式。 |
| [docs/ui.md](docs/ui.md) | 页面与交互规格。 |
| [docs/acceptance.md](docs/acceptance.md) | 验收用例和回归清单。 |
| [docs/system-design.md](docs/system-design.md) | 系统架构与设计边界。 |
| [docs/deployment.md](docs/deployment.md) | Docker 部署、升级、备份和故障排查。 |
| [ENVIRONMENT_BASELINE.md](ENVIRONMENT_BASELINE.md) | 工具版本、镜像标签和移植约定。 |
| [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) | 独立目录职责说明；其中部分旧状态需结合当前代码核对。 |

文档描述设计与验收要求，不代表所有设计目标均已实现；当前模块和文件职责以本 README 对照源码的说明为准。