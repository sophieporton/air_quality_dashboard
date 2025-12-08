import pandas as pd
import sqlite3
from PIL import Image


def add_sqlite_table(db, tablename, pk, not_null, column_order):
    """
    Create a SQLite table using sqlite-utils if it does not already exist.
    """
    try:
        db.table(
            tablename,
            pk=pk,
            not_null=not_null,
            column_order=column_order
        )
    except Exception as e:
        print(f"Warning: Could not create table '{tablename}' (it may already exist). Error: {e}")


def sql_to_pandas(db, sql_command):
    """
    Run an SQL query and return the result as a pandas DataFrame.
    """
    try:
        conn = sqlite3.connect(db)
        df = pd.read_sql(sql_command, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"SQL query failed: {e}")
        return pd.DataFrame()


def get_image(path: str) -> Image:
    """
    Load an image from disk.
    """
    try:
        return Image.open(path)
    except Exception as e:
        print(f"Could not load image: {path}. Error: {e}")
        return None


def delete_all_sql(conn, sql):
    """
    Execute a DELETE SQL command on a table.
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(f"Failed to delete rows: {e}")


def create_connection(db_file):
    """
    Create a connection to an SQLite database.
    """
    try:
        return sqlite3.connect(db_file)
    except Exception as e:
        print(f"Failed to connect to DB '{db_file}': {e}")
        return None
