from __future__ import annotations
import re
from typing import Any, Callable

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class Repository:
    """Small database access boundary used by the Streamlit application.

    Table/column identifiers are validated before interpolation. Values remain
    parameterized by the underlying SQLAlchemy layer.
    """
    def __init__(self, query_sql: Callable[..., Any], exec_sql: Callable[..., Any], cache_clear: Callable[[], None]):
        self.query_sql = query_sql
        self.exec_sql = exec_sql
        self.cache_clear = cache_clear

    @staticmethod
    def identifier(value: str) -> str:
        if not isinstance(value, str) or not IDENT_RE.fullmatch(value):
            raise ValueError(f"Unsafe SQL identifier: {value!r}")
        return value

    def select_all(self, table: str):
        return self.query_sql(f"select * from {self.identifier(table)}")

    def select_where(self, table: str, where_sql: str, params: dict | None = None):
        return self.query_sql(f"select * from {self.identifier(table)} where {where_sql}", params or {})

    def count(self, table: str, where_sql: str = "", params: dict | None = None) -> int:
        predicate = f" where {where_sql}" if where_sql else ""
        df = self.query_sql(f"select count(*) as n from {self.identifier(table)}{predicate}", params or {})
        return int(df.iloc[0]["n"]) if not df.empty else 0

    def insert(self, table: str, row: dict[str, Any]) -> None:
        table = self.identifier(table)
        cols = [self.identifier(c) for c in row]
        placeholders = [f":{c}" for c in cols]
        self.exec_sql(
            f"insert into {table} ({', '.join(cols)}) values ({', '.join(placeholders)})",
            row,
        )
        self.cache_clear()

    def insert_many(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        table = self.identifier(table)
        cols = [self.identifier(c) for c in rows[0]]
        if any(list(row) != list(rows[0]) for row in rows):
            raise ValueError("Bulk insert rows must have identical columns")
        placeholders = [f":{c}" for c in cols]
        self.exec_sql(
            f"insert into {table} ({', '.join(cols)}) values ({', '.join(placeholders)})",
            rows,
        )
        self.cache_clear()

    def update(self, table: str, id_col: str, id_val: str, row: dict[str, Any]) -> None:
        if not row:
            return
        table = self.identifier(table)
        id_col = self.identifier(id_col)
        cols = [self.identifier(c) for c in row]
        patch = dict(row)
        patch[id_col] = id_val
        sets = ", ".join(f"{c}=:{c}" for c in cols)
        self.exec_sql(f"update {table} set {sets} where {id_col}=:{id_col}", patch)
        self.cache_clear()

    def delete(self, table: str, id_col: str, id_val: str) -> None:
        table = self.identifier(table)
        id_col = self.identifier(id_col)
        self.exec_sql(f"delete from {table} where {id_col} = :id", {"id": id_val})
        self.cache_clear()

