# 环境基线

本文件是开发机与 Docker 运行机的版本基线。开发机原生安装工具；运行机通过 Docker Compose 使用同版本基础镜像构建并运行应用。版本变更须先评估并同步更新本文件、`.python-version`、`.nvmrc`、依赖锁文件及运行镜像标签。

## 开发机（Windows，原生运行）

| 项目 | 已核验版本/位置 | 用途 |
| --- | --- | --- |
| Python | `3.14.7` | Django 后端与测试。 |
| uv | `0.12.7` | Python 依赖及虚拟环境管理。 |
| Node.js | `24.19.0` | Vue/Vite 前端开发与构建。 |
| npm | `11.17.0` | 前端依赖安装与脚本执行。 |
| PostgreSQL | `18.6`，`D:\PostgreSQL` | 开发数据库。 |
| Docker Desktop / Docker Engine | 不安装 | 开发机不运行 Docker，也不要求 Docker 命令可用。 |

开发机后端、前端和 PostgreSQL 均在本机运行。数据库主机使用 `127.0.0.1`，数据库结构只能通过 Django migration 创建和升级。

## 运行机（Docker）

运行机需要 Docker Engine 与 Docker Compose 插件，但不要求预装 Python、Node.js 或 PostgreSQL。初始化项目后，Compose 必须使用下列固定基础镜像标签构建服务：

| 服务 | 固定基础镜像 | 版本来源 |
| --- | --- | --- |
| backend | `python:3.14.7-slim` | 开发机 Python。 |
| frontend build | `node:24.19.0-alpine` | 开发机 Node.js。 |
| database | `postgres:18.6` | 开发机 PostgreSQL。 |

`uv.lock` 锁定 Python 应用依赖，`package-lock.json` 锁定前端依赖，Django migrations 锁定数据库结构。运行机执行 `docker compose up --build -d` 时，后端容器必须先执行 migration；数据库数据使用命名 volume 保存。

## 配置与移植边界

- 提交：源码、`.python-version`、`.nvmrc`、本文件、`pyproject.toml`、`uv.lock`、`package.json`、`package-lock.json`、migrations、Dockerfile、Compose 文件及 `.env.example`。
- 不提交：`.env`、密钥、`.venv`、`node_modules`、构建产物、PostgreSQL 数据目录和业务备份。
- 开发机的 `.env` 使用 `DATABASE_HOST=127.0.0.1`；运行机 Compose 为后端覆盖为数据库服务名，例如 `DATABASE_HOST=db`。
- 移植业务数据使用 `pg_dump` 和 `pg_restore` 的逻辑备份；不得复制 PostgreSQL 数据目录。生产或验收迁移前先停止应用写入。

## 当前仓库状态
仓库已提供 Django、Vue、Dockerfile 和 Docker Compose 配置。开发机未安装 Docker，因此必须在安装 Docker Engine 与 Docker Compose 插件的运行机上执行构建验收。运行机只暴露前端 HTTP 端口；数据库与后端 API 位于 Docker 内部网络。详细操作见 [Docker 部署指南](docs/deployment.md)。