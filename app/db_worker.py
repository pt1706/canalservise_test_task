import inspect
from typing import List

import psycopg2.pool as pool
from psycopg2 import DatabaseError
from psycopg2.errors import UndefinedTable

from http_worker import Logger


class DBWorker(Logger):
    def __init__(self, host='db', database='orders'):
        self.pg_pool = pool.SimpleConnectionPool(
            1,
            2,
            host=host,
            port=5432,
            user='postgres',
            database=database,
            password='123'
        )

    def create_table(self) -> None:
        """
        Function create table in DB to save data
        """

        query = (
            'CREATE TABLE IF NOT EXISTS orders '
            '(id serial PRIMARY KEY, '
            'row_num integer, '
            'order_id integer UNIQUE, '
            'price_usd varchar, '
            'delivery_data varchar, '
            'price_rur varchar);'
        )

        try:
            conn = self.pg_pool.getconn()
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            cur.close()
            self.pg_pool.putconn(conn)

        except DatabaseError as e:
            self.write_log(inspect.stack()[0][3], e)
            return None

    def retrieve_orders_from_db(self):
        conn = self.pg_pool.getconn()
        cur = conn.cursor()

        try:
            cur.execute(
                """Select order_id FROM orders;""",
            )
            order_in_db = [order[0] for order in cur.fetchall()]
            return order_in_db

        except UndefinedTable as e:
            self.write_log(inspect.stack()[0][3], e)
            self.create_table()

        except DatabaseError as e:
            self.write_log(inspect.stack()[0][3], e)

        finally:
            cur.close()
            self.pg_pool.putconn(conn)
        return []

    def delete_orders_from_db(self, orders: List[int]) -> None:
        conn = self.pg_pool.getconn()
        cur = conn.cursor()
        query = 'DELETE from orders WHERE order_id IN %s;'
        try:
            cur.execute(
                query,
                (tuple(orders), ))
            conn.commit()

        except UndefinedTable as e:
            self.write_log(inspect.stack()[0][3], e)
            self.create_table()

        except DatabaseError as e:
            self.write_log(inspect.stack()[0][3], e)

        finally:
            cur.close()
            self.pg_pool.putconn(conn)

    def insert_order_in_db(self, order: List[int]):
        conn = self.pg_pool.getconn()
        cur = conn.cursor()
        query = 'INSERT INTO orders (row_num, order_id, ' \
                'price_usd, delivery_data, price_rur) ' \
                'VALUES (%s, %s, %s, %s, %s);'
        try:
            cur.execute(
                query,
                (*order, ))
            conn.commit()
            return 1
        except DatabaseError as e:
            self.write_log(inspect.stack()[0][3], e)
            return 0

        finally:
            cur.close()
            self.pg_pool.putconn(conn)

    def update_order_in_db(self, order):
        conn = self.pg_pool.getconn()
        cur = conn.cursor()
        query = 'UPDATE orders SET row_num = %s, ' \
                'price_usd = %s, delivery_data = %s, ' \
                'price_rur = %s WHERE order_id = %s;'
        try:
            cur.execute(
                query,
                (*order, ))
            conn.commit()
            return 1

        except DatabaseError as e:
            self.write_log(inspect.stack()[0][3], e)
            return 0

        finally:
            cur.close()
            self.pg_pool.putconn(conn)
