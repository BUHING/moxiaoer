# Docker 运行机部署指南

## 1. 运行机要求

运行机需要 64 位 Windows 或 Linux、Docker Engine 和 Docker Compose 插件。不要在运行机安装 Python、Node.js 或 PostgreSQL；这些依赖全部在容器镜像中。版本基线在 [环境基线](../ENVIRONMENT_BASELINE.md)：Python `3.14.7`、Node.js `24.19.0`、PostgreSQL `18.6`。

确认 Docker 可用：

```powershell
docker --version
docker compose version
```

将完整项目目录复制到运行机，例如 `D:\GrindBuddy`。必须同时带上 `backend/uv.lock`、`frontend/package-lock.json`、所有 Django migrations、`docker-compose.yml` 和 `infra/nginx/default.conf`。

## 2. 配置运行机环境

在运行机打开 PowerShell，进入项目目录：

```powershell
cd D:\GrindBuddy
Copy-Item .env.example .env
notepad .env
```

`.env` 中带“运行机必须修改”的三项必须在首次部署前替换：

| 配置项 | 如何填写 |
| --- | --- |
| `DJANGO_SECRET_KEY` | 使用至少 50 个随机字符。不要复用开发环境密钥。 |
| `DATABASE_PASSWORD` | 使用独立、高强度的数据库密码。首次启动后不要随意更改。 |
| `DJANGO_ALLOWED_HOSTS` | 保留 `localhost,127.0.0.1`，并增加运行机的局域网 IP 或 DNS 名称，例如 `localhost,127.0.0.1,192.168.1.50`。 |

按需修改以下项：

| 配置项 | 默认值 | 何时修改 |
| --- | --- | --- |
| `WEB_PORT` | `8080` | 端口冲突或需要用其他端口提供浏览器访问时修改。 |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8080` | 浏览器直接从独立前端域名调用 API 时增加完整来源。正常通过 Nginx 访问系统时无需修改。 |
| `DATABASE_NAME`、`DATABASE_USER` | `grindbuddy`、`grindbuddy_app` | 仅首次部署前按组织运维规范需要调整命名时修改。 |
| `PASSWORD_RESET_URL`、`DEFAULT_FROM_EMAIL`、`EMAIL_*` | 无 | 启用密码找回时必须配置可用 SMTP；重置链接应为用户可访问的 HTTPS 地址，SMTP 密码不得提交。 |

`.env` 是本机机密文件，不得提交、共享或复制至其他环境。系统的数据库密码不需要填入 `backend/.env`；Compose 会将根 `.env` 注入后端容器。

系统不使用超级账号。首次启用时，访问登录页并注册老板账号；每个老板账号独立管理自己的店铺和员工。

## 3. 首次启动

先检查 Compose 解析结果，确认不会显示未替换的占位值：

```powershell
docker compose config
```

首次构建并在后台启动：

```powershell
docker compose up --build -d
```

Compose 会依次创建 PostgreSQL 命名卷、启动并健康检查数据库、执行 Django migration、启动 Gunicorn 和 Nginx。正常情况下只有前端端口对运行机网络开放：`http://<运行机IP>:<WEB_PORT>`，默认示例为 `http://192.168.1.50:8080`。

## 4. 验证与日常运维

查看服务状态，三个服务都应显示为运行：

```powershell
docker compose ps
```

检查启动日志和 migration：

```powershell
docker compose logs --tail=100 db
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

从运行机验证 API：

```powershell
Invoke-WebRequest http://127.0.0.1:<WEB_PORT>/api/v1/health/ -UseBasicParsing
```

预期响应为 `{"data":{"status":"ok"}}`。然后用浏览器访问 `http://<运行机IP>:<WEB_PORT>/` 并完成一次 boss 注册和登录。

查看实时日志：

```powershell
docker compose logs -f
```

停止服务但保留数据库：

```powershell
docker compose down
```

重新启动已构建服务：

```powershell
docker compose up -d
```

Docker 服务重启后，Compose 中的 `restart: unless-stopped` 会自动恢复三个服务。

## 5. 升级应用

1. 先执行数据库逻辑备份。
2. 停止用户写入或安排维护窗口。
3. 用新版本项目文件替换代码，保留运行机已有的根 `.env` 文件。
4. 在项目根目录执行 `docker compose up --build -d`。
5. 查看 `docker compose logs --tail=100 backend`，确认 migration 与服务启动成功。
6. 重新执行健康检查与一次浏览器登录。

不要删除 `postgres_data` 命名卷；删除它会永久删除业务数据库。

### 客户、供应商组合判重升级

`partners.0006_partner_identity_unique` 将旧的“组织内名称唯一”替换为组合身份唯一。客户比较名称、联系人、电话；供应商另比较联系地址。迁移先只读检查现有资料，再建立新组合索引，最后移除旧名称限制，整个迁移在事务中执行。不会修改现有字段、UUID、单据关联或库存数据；若发现按新规则完全相同的旧资料，则停止迁移并明确报错，不会自动合并或删除。

此升级必须先备份并在独立测试库验证可恢复性，安排暂停业务写入后统一部署前后端；仅更新前端或不执行迁移，不能启用新规则。升级后对比客户、供应商、商品、单据和库存等业务记录数及内容，迁移记录表按正常流程增加记录。若已经产生合法同名资料，不得直接回退旧名称唯一约束，更不能为回退而删除资料；须单独评估回退方案。

## 6. 数据库备份与恢复

创建带日期的逻辑备份：

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
docker compose exec -T db pg_dump -U grindbuddy_app -d grindbuddy -Fc > backups\grindbuddy-YYYYMMDD.backup
```

实际部署中应将命令中的数据库名和用户替换成 `.env` 中的 `DATABASE_NAME`、`DATABASE_USER`。备份文件包含业务数据，应加密保存到受控位置并定期验证可恢复性。

恢复操作会覆盖数据，必须先停止后端写入并确认目标数据库可被清空。恢复前先咨询负责数据的人员；不要将未验证的备份直接恢复到正在使用的运行机。

## 7. 故障排查

| 现象 | 检查与处理 |
| --- | --- |
| `docker compose up` 提示变量未设置 | 检查根 `.env` 是否存在，且 `DJANGO_SECRET_KEY` 与 `DATABASE_PASSWORD` 已替换。 |
| 浏览器返回 `400 Bad Request` | 在 `.env` 的 `DJANGO_ALLOWED_HOSTS` 添加浏览器实际访问的 IP 或 DNS 名称，随后执行 `docker compose up -d --force-recreate backend`。 |
| 浏览器无法访问 | 执行 `docker compose ps`；确认 Windows 防火墙或 Linux 防火墙允许 `WEB_PORT` 入站访问。 |
| 后端无法连接数据库 | 执行 `docker compose logs backend db`；首次初始化时，确认没有保留由旧密码创建的 `postgres_data` 卷。 |
| 端口冲突 | 修改 `.env` 的 `WEB_PORT` 后运行 `docker compose up -d --force-recreate frontend`。 |