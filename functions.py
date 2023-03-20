#%%
import pandas as pd
import sqlite3
from PIL import Image


#%%
def add_sqlite_table(db,tablename, pk, not_null, column_order):
    table=db.table(
        tablename,
        pk=pk,
        not_null=not_null,
        column_order=column_order

    )
# %%

def sql_to_pandas(db, sql_command,):
    '''turns sqlite database into a pandas dataframe'''

    conn= sqlite3.connect(db)
    sql= sql_command
    data = pd.read_sql(sql, conn)
    
    return data


# %%
def get_image(path:str)->Image:
    image = Image.open(path)
    return image

#%%
def delete_all_tasks(conn):
    """
    Delete all rows in the tasks table
    :param conn: Connection to the SQLite database
    :return:
    """
    sql = 'DELETE FROM NO2_hourly'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

#%%
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = sqlite3.connect(db_file)

    return conn
# %%
