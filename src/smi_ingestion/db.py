"""Small PostgreSQL connection factory shared by ingestion modules."""

from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


class Database:
    def __init__(self, dsn: str, schema: str | None = None):
        self.dsn = dsn
        self.schema = schema

    def connect(self):
        connection = psycopg.connect(self.dsn, row_factory=dict_row)
        if self.schema:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        return connection

    def migrate(self) -> None:
        ddl = Path(__file__).with_name("schema.sql").read_text()
        with self.connect() as connection:
            connection.execute(ddl)
