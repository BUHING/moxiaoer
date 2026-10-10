# API Client 边界

`generated/` 只保存由 OpenAPI 生成器写入的类型和 Client，禁止手工修改。执行 `npm run generate:api` 从 Django 的 `/api/schema/` 同步契约；手写的 Axios 配置、拦截器和请求基础设施放在 `http/`。