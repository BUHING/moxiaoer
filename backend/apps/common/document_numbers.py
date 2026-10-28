import sqlite3
from itertools import count
from zoneinfo import ZoneInfo

from django.db import IntegrityError, models, transaction
from django.utils import timezone

NUMBER_TIME_ZONE = ZoneInfo("Asia/Shanghai")


def _is_number_conflict(error: IntegrityError, document) -> bool:
    constraint_name = next(
        constraint.name
        for constraint in document._meta.constraints
        if isinstance(constraint, models.UniqueConstraint)
        and constraint.fields == ("organization", "document_no")
    )
    cause = error.__cause__
    diagnostic = getattr(cause, "diag", None)
    if diagnostic is not None:
        return diagnostic.constraint_name == constraint_name

    table = document._meta.db_table
    return isinstance(cause, sqlite3.IntegrityError) and str(cause) == (
        f"UNIQUE constraint failed: {table}.organization_id, {table}.document_no"
    )


def save_document_with_number(*, document, prefix: str) -> None:
    if not document._state.adding:
        raise ValueError("Only new documents may receive a document number.")
    timestamp = timezone.localtime(timezone.now(), NUMBER_TIME_ZONE).strftime("%Y%m%d%H%M%S")
    base = f"{prefix}{timestamp}"

    for sequence in count(1):
        document.document_no = base if sequence == 1 else f"{base}-{sequence:02d}"
        try:
            # A savepoint keeps a numbering collision from breaking the creation transaction.
            with transaction.atomic():
                document.save(force_insert=True)
            return
        except IntegrityError as error:
            if not _is_number_conflict(error, document):
                raise
