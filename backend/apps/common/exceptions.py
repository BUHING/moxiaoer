from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    errors = response.data if isinstance(response.data, dict) else {}
    detail = errors.get("detail")
    message = str(detail) if detail else "请求校验失败。"
    normalized_errors = {
        field: [str(item) for item in items] if isinstance(items, list) else [str(items)]
        for field, items in errors.items()
        if field != "detail"
    }
    code = detail.code if isinstance(detail, ErrorDetail) else "request_error"
    response.data = {
        "code": code,
        "message": message,
        "errors": normalized_errors,
        "request_id": None,
    }
    return response