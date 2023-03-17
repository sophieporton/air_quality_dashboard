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