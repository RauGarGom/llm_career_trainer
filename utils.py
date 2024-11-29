import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv, find_dotenv
import os
from model import db_connect

load_dotenv(override=True)

def restore_db():
    conn,cursor = db_connect()
    cursor.execute('''DROP TABLE regist;''')
    create_table = '''
    CREATE TABLE regist (
        id SERIAL PRIMARY KEY,
        action TEXT,
        llm_user TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    cursor.execute(create_table)
    conn.commit()
    conn.close()
