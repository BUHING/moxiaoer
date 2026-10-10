# Django 应用边界

每个 app 预留 `models.py`、`serializers.py`、`views.py`、`urls.py`、`services.py`、`permissions.py` 和 `tests/` 的位置；只有开始实现已确认规则时才创建对应代码文件。

- `common` 提供跨应用技术能力，目前包含 API 根与健康检查。
- `accounts`、`products`、`partners`、`inventory`、`purchases`、`sales`、`reports` 对应已确认首期模块。
- `warehouses`、`stocktaking`、`transfers` 仅保留边界，均是首期范围外，不能据此实现业务能力。
- `system` 用于将来的操作日志和系统配置，具体范围尚未确认。

库存、单据完成、作废、退货、盘点和调拨的写入规则必须位于所属 app 的 `services.py`，并以 `docs/` 中已确认规则为准。