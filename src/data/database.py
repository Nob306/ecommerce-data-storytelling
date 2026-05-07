
import os
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    host:     str = os.getenv("POSTGRES_HOST", "localhost")
    port:     int = int(os.getenv("POSTGRES_PORT", "5432"))
    dbname:   str = os.getenv("POSTGRES_DB",   "ecommerce_analytics")
    user:     str = os.getenv("POSTGRES_USER", "analytics_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "analytics_dev")

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.dbname} "
            f"user={self.user} password={self.password}"
        )

    def __repr__(self) -> str:
        return (
            f"DatabaseConfig(host={self.host}, port={self.port}, "
            f"dbname={self.dbname}, user={self.user})"
        )

@contextmanager
def get_connection(config: Optional[DatabaseConfig] = None):
    """
    Context manager that yields a psycopg2 connection and
    commits on clean exit, rolls back on exception.

    Example:
        with get_connection() as conn:
            df = pd.read_sql(query, conn)
    """
    cfg = config or DatabaseConfig()
    conn = None
    try:
        conn = psycopg2.connect(cfg.dsn)
        logger.debug(f"Connected to {cfg.dbname} at {cfg.host}:{cfg.port}")
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def test_connection(config: Optional[DatabaseConfig] = None) -> bool:
    """Returns True if the database is reachable, False otherwise."""
    try:
        with get_connection(config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def execute_query(
    sql: str,
    params: Optional[tuple] = None,
    config: Optional[DatabaseConfig] = None
) -> pd.DataFrame:
    """
    Run a SELECT and return results as a DataFrame.

    Example:
        df = execute_query(
            "SELECT * FROM anomalies WHERE severity = %s",
            params=('HIGH',)
        )
    """
    with get_connection(config) as conn:
        return pd.read_sql(sql, conn, params=params)


def insert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    conn,
    conflict_action: str = "DO NOTHING"
) -> int:
    """
    Bulk insert a DataFrame into a table using execute_values (fast path).

    Args:
        df:              DataFrame whose columns match the target table.
        table_name:      Target table name.
        conn:            Active psycopg2 connection.
        conflict_action: ON CONFLICT action — 'DO NOTHING' or a full
                         'DO UPDATE SET ...' clause.

    Returns:
        Number of rows inserted.

    Example:
        with get_connection() as conn:
            n = insert_dataframe(kpi_df, 'kpi_results', conn)
            print(f"Inserted {n} rows")
    """
    if df.empty:
        logger.warning(f"insert_dataframe: empty DataFrame, skipping {table_name}")
        return 0

    columns = list(df.columns)
    col_str = ", ".join(columns)
    placeholder = f"INSERT INTO {table_name} ({col_str}) VALUES %s ON CONFLICT {conflict_action}"

    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

    with conn.cursor() as cur:
        execute_values(cur, placeholder, rows)
        count = cur.rowcount

    logger.info(f"Inserted {count} rows into {table_name}")
    return count


def upsert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    conflict_columns: list[str],
    update_columns: list[str],
    conn
) -> int:
    """
    Upsert a DataFrame — insert new rows, update existing ones on conflict.

    Args:
        df:                DataFrame to upsert.
        table_name:        Target table name.
        conflict_columns:  Columns that define uniqueness (the ON CONFLICT target).
        update_columns:    Columns to update when a conflict occurs.
        conn:              Active psycopg2 connection.

    Example:
        upsert_dataframe(
            df=kpi_df,
            table_name='kpi_results',
            conflict_columns=['kpi_name', 'week_date'],
            update_columns=['value', 'computed_at'],
            conn=conn
        )
    """
    if df.empty:
        return 0

    columns = list(df.columns)
    col_str = ", ".join(columns)
    conflict_str = ", ".join(conflict_columns)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_columns)

    sql = (
        f"INSERT INTO {table_name} ({col_str}) VALUES %s "
        f"ON CONFLICT ({conflict_str}) DO UPDATE SET {update_str}"
    )

    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
        count = cur.rowcount

    logger.info(f"Upserted {count} rows into {table_name}")
    return count

def table_row_count(table_name: str, config: Optional[DatabaseConfig] = None) -> int:
    """Returns the number of rows in a table."""
    df = execute_query(f"SELECT COUNT(*) AS n FROM {table_name}", config=config)
    return int(df["n"].iloc[0])


def truncate_table(table_name: str, conn) -> None:
    """Truncates a table. Use with care — irreversible."""
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
    logger.warning(f"Truncated {table_name}")

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ok = test_connection()
    sys.exit(0 if ok else 1)