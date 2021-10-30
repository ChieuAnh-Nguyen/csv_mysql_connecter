import os
import re
import pandas as pd
import mysql.connector
import credentials as cred
# Since changes were made in cred and our ipynb can't see new changes, we use Importlib to reload the module
import importlib
importlib.reload(cred)


def create_csv_list():
    """add csv's in current directory to a list
    re.sub(r'[^\w\.]', '_', csv) substitutes all non word and num characters

    """
    csv_files = []
    for csv in os.listdir(os.getcwd()):
        if '.csv' in csv:
            old_csv_name = str(os.getcwd() + '/' + csv)
            csv = re.sub(r'[^\w\.]', '_', csv).lower()
            #if csv in cwd, move csv to new folder
            new_csv_name = str(os.getcwd() + '/' + csv)
            if os.path.isfile(new_csv_name):
                pass
            else:
                # Rename the file
                os.rename(old_csv_name, new_csv_name)
            csv_files.append(csv)
    return csv_files

def change_directory(csv_files,new_directory):
    """Create new folder in current directory and move files to new directory"""
    try:
        os.mkdir(new_directory)
    except:
        pass
    for csv in csv_files:
        mv = "mv '{0}' {1}".format(csv,new_directory)
        os.system(mv)
    return

def create_dict(csv_files, new_directory):
    """Create dictionary with csv name as key and df as value"""
    df_dict = {}
    for csv in csv_files:
        csv_path = str(os.getcwd() + '/' + new_directory + '/' + csv)
        df_dict[csv] = pd.read_csv(csv_path, index_col = 0)
    return df_dict

def clean_columns(dataframe):
    """cleans column names and changes pd datatypes to sql datatypes"""
    dataframe_columns = [re.sub(r'[^\w\.]', '_', column_name).lower() for column_name in dataframe.columns]
    replacements = {
        'timedelta64[ns]': 'varchar(255)',
        'object': 'varchar(255)',
        'float64': 'float',
        'bool': 'boolean',
        'int64': 'int',
        'datetime64': 'timestamp'}
    replaced_dtypes = dataframe.dtypes.replace(replacements)
    # table schema
    column_dtype = ", ".join("{} {}".format(col_name, dtype) for (col_name, dtype) in zip(dataframe_columns, replaced_dtypes))

    return dataframe_columns, column_dtype

def connect_to_mysql(host,user,password,database):
    """Connects to mysql db"""
    conn = mysql.connector.connect(host = host,
    user = user, 
    password = password,
    database = database)
    return conn

def upload_csv_to_DB(conn,dataframe, key, dataframe_columns,column_dtype):
    """Creates DB table name"""
    cursor = conn.cursor(buffered=True)
    db_table_name = key.split('.')[0]
    #dataframe.columns as a str
    dataframe_columns_insertable = ', '.join(dataframe_columns)
    # create queries
    drop_table = 'DROP TABLE IF EXISTS ' + db_table_name
    create_table = 'CREATE TABLE ' + db_table_name + " (" + column_dtype + ")"
    insert_into_table = 'INSERT INTO ' + db_table_name + '(' + dataframe_columns_insertable + ')' \
    +' VALUES ( %s' % ', '.join(['%s'] * len(dataframe_columns)) +')'

    select_table = 'SELECT * FROM ' + db_table_name
    cursor.execute(drop_table)
    cursor.execute(create_table)
    # create insert into function
    for index, row in dataframe.iterrows():
        row = tuple(row)
        cursor.execute(insert_into_table,row)
        
    conn.commit()

    # Show table in DB
    cursor.execute(select_table)
    for each in cursor:
        print(each)
    
    cursor.close()
