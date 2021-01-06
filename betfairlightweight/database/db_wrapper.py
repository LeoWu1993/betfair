import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple, Union

class PgConnector:

    def __init__(self):
        self.host = "localhost"
        self.user = "postgres"
        self.password = "Wty200801="
        self.database = "postgres"
        self.port = "5432"
        self.conn_args = {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "port": self.port,
        }

    @staticmethod
    def chunk_list(l, size):
        size = max(1, size)
        return (l[i : i + size] for i in range(0, len(l), size))

    def execute_query(self, query:str, select_query: bool=True) -> list:
        conn = psycopg2.connect(**self.conn_args)
        #print("Database Connected....")
        cur = conn.cursor()
        cur.execute(query)
        if select_query:
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        else:
            conn.commit()
            cur.close()
            conn.close()

    def insert_to_table(self, values: Union[List, Tuple], schema: str, table: str, chunk_size=10000):
        conn = psycopg2.connect(**self.conn_args)
        print("Database Connected....")
        cur = conn.cursor()
        full_table_name = f"{schema}.{table}"

        for chunked_values in self.chunk_list(values, chunk_size):
            dat_all = chunked_values
            execute_values(cur, "insert into {} values %s".format(full_table_name), dat_all)
            conn.commit()
        cur.close()
        conn.close()