import pandas as pd
import psycopg2
from sqlalchemy import create_engine

class PostgresSQLClient:
    def __init__(self, database, user, password, host="127.0.0.1", port="5432"):
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def create_conn(self):
        conn = psycopg2.connect(
            database = self.database,
            user = self.user,
            password = self.password,
            host = self.host,
            port = self.port
        )

        return conn

    def execute_query(self, query, data=None):
        conn = self.create_conn()
        cursor = conn.cursor()
        if data is None:
            cursor.execute(query)
        else:
            cursor.execute(query, data)
        conn.commit()
        conn.close()

    def get_columns(self, table_name):
        engine = create_engine(
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}/{self.database}"
        )
        conn = engine.connect()
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        return df.columns