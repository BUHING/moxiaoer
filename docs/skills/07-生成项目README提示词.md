# 生成 `README.md` 的提示词

```text
你是一名全栈项目维护者。以 `docs/功能模块设计.docx` 为功能范围主文档，以已确认的 `docs/system-design.md` 为最终技术设计基线，并根据 `docs/requirements.md`、`docs/domain-rules.md`、`docs/data-model.md`、`docs/api.md`、`docs/ui.md` 和 `docs/acceptance.md`，为本仓库生成根目录 README.md。只输出 Markdown 正文。README 面向开发人员和使用 AI 协作开发的维护者；不要声称任何尚未实现的功能或命令。

主文档文字决定项目范围和首期模块，参考图不构成已实现或待实现功能。若 `system-design.md` 尚未生成或未确认，README 必须明确标记 TODO，而不是把推测写成事实。

## 确定技术栈
- 后端：Python、Django、Django REST Framework、drf-spectacular、SimpleJWT。
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Axios、TanStack Query for Vue。
- 数据库：PostgreSQL。
- 开发：Windows 本机安装 Python、Node.js 和 PostgreSQL，不安装 Docker。
- 运行机部署：Docker Compose，以根目录 `ENVIRONMENT_BASELINE.md` 的固定镜像版本为准。
- 测试：pytest、pytest-django；前端测试工具仅在项目已实际配置时写入。
- 代码质量：Ruff；mypy 仅在项目实际启用时写入。

## README 必须包含
1. 项目简介、目标用户和功能边界。
2. 技术架构图：使用 Mermaid 展示开发机原生 Vue、Django REST API、PostgreSQL 与运行机 Docker Compose 的关系。
3. 仓库目录约定；若目录尚未初始化，使用“目标结构”措辞。
4. 本地前置条件、环境变量说明和安全规则。不得把真实密码、JWT 密钥或生产连接串写入示例。
5. 开发机原生启动步骤与运行机 Docker Compose 启动步骤。若尚未有实际命令，将命令标记为“初始化后补充”，不得编造；不得要求开发机安装 Docker。
6. 数据库迁移、创建管理员、测试、代码检查、生成 OpenAPI/前端类型的工作流；只列出已确定或可由项目配置验证的命令。
7. 业务不变量摘要：基于主文档实际范围说明库存流水、金额精度、审核/作废、boss/employee 数据隔离、权限和事务要求，并链接到 `docs/domain-rules.md` 与 `docs/system-design.md`。
8. API 文档地址约定、前后端类型同步规则、模块开发流程。
9. 数据备份与恢复建议，特别说明单机部署的数据库备份责任。
10. AI 协作规则：先阅读 `docs/功能模块设计.docx`、`docs/system-design.md` 和关联规格；不绕过领域规则；实现前补充或更新测试；不手工复制 API DTO；修改规则时同步更新主文档、最终设计说明书和关联规格。

使用清晰简洁的中文。对于仍未决定或未实现的内容显式标记 TODO，不得把推测描述为已完成事实。
```
