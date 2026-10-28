# 磨小二进销存系统 API 规范

## 1. 通用约定

根路径为 `/api/v1/`，JSON 字段为 `lower_snake_case`。受保护请求使用 `Authorization: Bearer <jwt>`；库存或单据完成动作须带唯一 `Idempotency-Key`。日期时间为 ISO 8601 UTC；金额和高精度数量为字符串。列表使用 `page`、`page_size`、`ordering`、`search`，默认按创建时间倒序；未定义的筛选和排序不得依赖。

成功响应使用 `{ "data": ..., "meta": ... }`，错误使用 `{ "code": "...", "message": "...", "errors": { "field": ["..."] }, "request_id": "..." }`。状态码：400 参数错误、401 未认证、403 无权限/跨组织、404 不存在、409 状态/幂等/并发冲突或库存不足、500 未预期错误。

## 2. 认证与设置

| 方法与路径 | 用途 | 权限/规则 |
| --- | --- | --- |
| `POST /auth/register/` | 注册 boss | 仅用户名、密码；AUTH-001。 |
| `POST /auth/token/` | 用户名密码登录 | boss 或被创建的 employee。 |
| `POST /auth/token/refresh/` | 刷新 JWT | 有效 refresh token。 |
| `GET /auth/me/` | 当前用户、组织、角色、有效权限 | 已认证。 |
| `GET,POST /employees/` | 列表/创建 employee | boss；AUTH-001。 |
| `GET,PATCH /employees/{id}/` | 查询/维护 employee | boss，且限本组织。 |
| `GET,POST /permission-requests/` | employee 查询/提交申请；boss 查询 | AUTH-003。 |
| `POST /permission-requests/{id}/approve/` | 批准申请 | boss；AUTH-003。 |
| `POST /permission-requests/{id}/reject/` | 拒绝申请 | boss；AUTH-003。 |
| `GET,PUT /shop-profile/` | 获取/维护店铺 | boss 写；employee 读权限待确认。 |

## 3. 基础资料

客户和供应商的名称允许重复。客户以当前组织内的 `name + contact_name + phone` 判重；供应商以 `name + contact_name + contact_address + phone` 判重，包含停用资料且忽略首尾空格。可选字段缺省视为空字符串，PATCH 结合现有字段判断并排除当前记录。重复的 POST/PATCH 分别返回 `409 duplicate_customer` 或 `409 duplicate_supplier`，沿用统一错误响应结构，`message` 包含可理解的中文说明；若冲突资料已停用，提示切换“仅停用”查看。不自动规范化内部空格、电话标点或区号，不以备注区分身份。失败保存不得部分更新资料。

`/products/`、`/units/`、`/specifications/`、`/product-attributes/`、`/price-levels/`、`/customers/`、`/suppliers/` 支持受权限约束的列表与草稿资料 CRUD；`/products/{id}/prices/` 查询价格。选择型商品属性的可选项使用嵌套资源 `GET,POST /product-attributes/{attribute_id}/options/` 和 `PATCH,DELETE /product-attributes/{attribute_id}/options/{option_id}/` 管理。删除已引用资料应返回 `409 resource_in_use`，停用使用 `POST /{resource}/{id}/deactivate/`。所有列表可用 `is_active` 筛选和 `search`；商品可额外按 `unit_id`、`price_level_id` 筛选。供应商请求体中的 `name` 为创建必填项，可选 `contact_name`、`contact_address`、`phone` 和 `remark`。

商品创建请求包含 `name`、`unit_id`，可包含 `supplier_id`、`initial_quantity`、`specification_values`、`attribute_values` 和 `prices`。`supplier_id` 是可选默认供应商，必须为当前组织的启用供应商，商品读取结果返回 `supplier_id`、`supplier_name`；它不影响采购单中单独选择的供应商。规格值使用 `{specification_id, value}`；文本属性使用 `{attribute_id, text_value}`，选择型属性使用 `{attribute_id, option_id}`；价格使用 `{price_level_id, amount}`。`initial_quantity` 仅能在创建时提供，后端须转化为 `INITIAL` 流水（INV-004），不得暴露库存余额写接口。价格等级创建或启用超过六个应返回 `409 price_level_limit`（MD-003）。

## 4. 单据与库存

| 方法与路径 | 用途 | 权限/规则 |
| --- | --- | --- |
| `GET,POST /purchases/`；`GET,PATCH /purchases/{id}/` | 进货草稿 | 进货权限；DOC-001。 |
| `POST /purchases/{id}/complete/` | 完成进货入库 | INV-001、DOC-002、CON-001。 |
| `GET,POST /purchase-returns/`；`POST /purchase-returns/{id}/complete/` | 进货退货草稿/完成 | 进货退货权限；INV-001。 |
| `GET,POST /sales-orders/`；`GET,PATCH /sales-orders/{id}/` | 销售草稿 | 销售开单权限；DOC-001。 |
| `POST /sales-orders/{id}/complete/` | 完成销售出库 | INV-001、INV-006、CON-001。 |
| `GET,POST /sales-returns/`；`POST /sales-returns/{id}/complete/` | 销售退货草稿/完成 | 销售退货权限；INV-001。 |
| `GET /inventory/balances/` | 当前库存 | 查询权限；只读。 |
| `GET /inventory/movements/` | 库存流水 | 查询权限；只读、可按 `product_id`、`movement_type`、日期筛选。 |

商品创建与更新体支持非负的两位小数 `purchase_price`，商品读取结果返回该字段。销售与销售退货创建体为 `{customer_id, occurred_on, items:[{product_id, quantity, unit_price}]}`，三个字段均必填；数量为四位小数、单价为两位小数。完成后明细额外返回只读的 `unit_cost_snapshot` 与六位小数 `cost_amount`。`line_amount`、`total_amount`、库存、状态和完成审计字段只读。完成成功返回单据；重复相同幂等键返回首次结果，不重放库存变化；销售库存不足返回 `409 insufficient_stock`。草稿可 PATCH，完成单据 PATCH 返回 `409 sales_conflict`。作废、反审核和原单退货关联尚未确认，暂不定义端点。

## 5. 分析与首页

| 方法与路径 | 用途 | 权限 |
| --- | --- | --- |
| `GET /reports/sales/` | 销售数量、单数、金额、销售/退货/净成本及毛利 | 查询权限。 |
| `GET /reports/purchases/` | 进货数量和金额 | 查询权限。 |
| `GET /reports/inventory/` | 当前库存统计 | 查询权限。 |
| `GET /dashboard/` | 今日/本周/本月销售单数、销售额、毛利及上月对比 | 查询权限。 |

销售与进货统计要求同时提供 ISO 日期参数 `date_from`、`date_to`，按单据业务日期统计已完成单据。销售返回完成销售单数、销售/退货/净销售数量和金额，销售退货冲减净数据；进货返回完成进货单数、进货/退货/净进货数量和金额。库存统计返回当前库存商品总数、有库存/无库存商品数和库存总数量，不接受日期参数。所有统计均限定当前组织，数量和金额分别使用四位、两位小数字符串。

销售成本使用明细完成时的成本快照。销售统计返回销售成本、退货成本、净销售成本与毛利；首页 `gross_profit` 返回同一口径的金额。独立销售退货使用其完成时的商品进货价，直到后续定义原销售单关联。

## 6. 兼容与待确认

`/api/v1/` 只允许新增可选字段和端点；破坏性变更使用新版本。未确认：单据正式状态/作废动作、负库存错误细节、字段精度/税务、完整资料字段、筛选排序白名单、店铺 employee 权限和统计时区/成本口径。Schema 由 drf-spectacular 生成，前端类型与 Client 必须由 OpenAPI 生成。