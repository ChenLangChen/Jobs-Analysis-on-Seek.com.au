"""碎碎念 Now I need to convert it to a module with functions 🌸"""
from sqlalchemy import *
import json
import sqlalchemy
from urllib.parse import quote_plus
import pandas as pd

def make_connection(db_name):
    # DATABASE SETTINGS
    db_credentials_file = "../credentials/freddy_credentials.json"
    database = db_name # "scrap"

    dialect="mysql"
    driver="pymysql"

    # Open credentials JSON file as a dictionary
    with open(db_credentials_file, "r") as fob:
        credentials = json.load(fob)

    # Extract credentials information, and escape special URL unsafe characters
    user = quote_plus(credentials["user"])
    host = quote_plus(credentials["host"])
    password = quote_plus(credentials["password"])
    port = credentials["port"]

    # Create URI address for the database
    uri = f"{dialect}+{driver}://{user}:{password}@{host}:{port}/{database}"
    # Create database connection engine
    engine = sqlalchemy.create_engine(uri, pool_timeout=30)

    return engine

def get_query_dict(column_list, value_list):
    """Function to construct the query dictionary given columns of a table and the values to be inserted"""
    entry_dict = {}
    for i in range(len(column_list)):
        entry_dict.update({column_list[i] : value_list[i]})
    return entry_dict

def get_tables(engine):
    """Function to retrieve table objects"""
    metadata = MetaData(bind=engine)
    metadata.reflect()

    table_list = list()
    for t in metadata.sorted_tables:
        table_list.append(t)
    return table_list

def insert_value(engine, table_list, table_index, query_dict):
    with engine.begin() as con:
       result = con.execute(table_list[table_index].insert(),[query_dict])

def make_query(engine, q):
    """Function to make a query and return the result as dataframe"""
    df = pd.read_sql_query(q, con=engine)
    return df

# engine = make_connection('scrap')
# q = "select * from seek limit 100 ;"
# my_df = make_query(engine, q)
# my_df.head(5)
# my_df.to_csv(r'alchemy_mod/seek_sample.csv')

###########################################
