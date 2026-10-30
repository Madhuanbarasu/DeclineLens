"""Database access. Exasol Personal is the target platform; DuckDB is only a local stand-in so
the same SQL can be tested on a laptop without a database. The SQL files are identical."""
import os
import re
import ssl
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
SCHEMA = "declinelens"


def split_sql(text: str):
    text = re.sub(r"--[^\n]*", "", text)
    return [s.strip() for s in text.split(";") if s.strip()]


class DB:
    def __init__(self, backend: str = "duckdb", path: str = None, read_only: bool = False):
        self.backend = backend
        if backend == "duckdb":
            import duckdb
            self.path = path or os.environ.get("DECLINELENS_DB", str(ROOT / "data" / "local_test.duckdb"))
            if self.path != ":memory:":
                Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self.con = duckdb.connect(self.path, read_only=read_only)
        elif backend == "exasol":
            import pyexasol
            opts = {}
            if os.environ.get("EXASOL_VERIFY_CERT", "0") != "1":
                opts["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}   # self-signed by default
            self.con = pyexasol.connect(
                dsn=os.environ["EXASOL_DSN"], user=os.environ["EXASOL_USER"],
                password=os.environ["EXASOL_PASSWORD"], encryption=True, **opts)
        else:
            raise ValueError(f"unknown backend {backend}")

    def execute(self, sql: str):
        self.con.execute(sql)

    def query(self, sql: str) -> pd.DataFrame:
        if self.backend == "duckdb":
            df = self.con.execute(sql).df()
        else:
            df = self.con.export_to_pandas(sql)
        df.columns = [c.lower() for c in df.columns]
        return df

    def load_df(self, df: pd.DataFrame, table: str):
        if self.backend == "duckdb":
            self.con.register("df_tmp", df)
            self.con.execute(f"INSERT INTO {SCHEMA}.{table} SELECT * FROM df_tmp")
            self.con.unregister("df_tmp")
        else:
            self.con.import_from_pandas(df, (SCHEMA.upper(), table.upper()))

    def run_script(self, name: str) -> float:
        t0 = time.perf_counter()
        for stmt in split_sql((SQL_DIR / name).read_text()):
            self.execute(stmt)
        return time.perf_counter() - t0

    def scalar(self, sql: str):
        return self.query(sql).iloc[0, 0]

    def close(self):
        self.con.close()
