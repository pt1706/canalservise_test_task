import unittest

import psycopg2
from psycopg2 import DatabaseError

from app.db_worker import DBWorker


class DbTest(unittest.TestCase):
    """
    Base class encapsulate attrs and methods to handle DB
    """
    conn = psycopg2.connect(
        database='orders_test',
        host='db',
        user='postgres',
        password='123'
    )
    worker = DBWorker(database='orders_test', host='db')

    @classmethod
    def _crate_table(cls):
        query_create = (
            'CREATE TABLE IF NOT EXISTS orders '
            '(id serial PRIMARY KEY, '
            'row_num integer, '
            'order_id integer UNIQUE, '
            'price_usd varchar, '
            'delivery_data varchar, '
            'price_rur varchar);'
        )
        with cls.conn.cursor() as cur:
            cur.execute(query_create)
            cls.conn.commit()

    @classmethod
    def _populate_table(cls):
        query = 'INSERT INTO orders (row_num, order_id, ' \
                'price_usd, delivery_data, price_rur) ' \
                'VALUES (%s, %s, %s, %s, %s);'
        orders = [(1, x, 500, '12.04.2023', 5000) for x in range(10)]

        with cls.conn.cursor() as cur:
            cur.executemany(query, orders)
            cls.conn.commit()

    @classmethod
    def _delete_table(cls):
        query = """DROP TABLE IF EXISTS orders;"""
        with cls.conn.cursor() as cur:
            cur.execute(query)
            cls.conn.commit()

    @classmethod
    def _truncate_table(cls):
        query = """TRUNCATE TABLE orders;"""
        with cls.conn.cursor() as cur:
            cur.execute(query)
            cls.conn.commit()


class TestDBWorker(DbTest):
    """
    testcases for testing DBWorker
    """

    def setUp(self) -> None:
        self._delete_table()
        self._crate_table()
        self._populate_table()

    def tearDown(self) -> None:
        self._delete_table()

    def test_retrieve_orders_from_db(self):
        """
        testing successful retrieving orders from db
        """
        res = self.worker.retrieve_orders_from_db()
        self.assertEqual(10, len(res))
        self.assertIn(1, res)
        self.assertNotIn(11, res)

    def test_retrieve_orders_from_db_negative(self):
        """
        testing retrieving orders from db when db or table doesn't exist
        """
        with self.assertRaises(DatabaseError):
            DBWorker(
                database='invalid', host='127.0.0.1'
            ).retrieve_orders_from_db()

        self._delete_table()
        res = self.worker.retrieve_orders_from_db()
        self.assertEqual([], res)

        query = 'SELECT EXISTS(SELECT * FROM '\
                'information_schema.tables WHERE table_name=%s)'
        cur = self.conn.cursor()
        cur.execute(query, ('orders',))
        self.assertTrue(cur.fetchone()[0])

    def test_delete_orders_from_db(self):
        """
        testing deleting orders from DB
        """
        orders = [x for x in range(10)]
        self.worker.delete_orders_from_db(orders)
        query = 'SELECT * FROM orders;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.assertEqual(0, len(cur.fetchall()))

    def test_insert_order_in_db(self):
        """
        testing inserting orders in DB
        """
        order = [1, 11, 500, '12.04.2023', 5000]
        res = self.worker.insert_order_in_db(order)
        self.assertEqual(1, res)

        query = 'SELECT * FROM orders;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.assertEqual(11, len(cur.fetchall()))

    def test_insert_order_in_db_negative(self):
        """
        testing inserting with negative output
        - order_id already in table
        - incorrect data type
        - incorrect order of args
        """
        order = [1, 9, 500, '12.04.2023', 5000]
        res = self.worker.insert_order_in_db(order)
        self.assertEqual(0, res)
        query = 'SELECT * FROM orders;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.assertEqual(10, len(cur.fetchall()))

        self._truncate_table()
        order = [1, '11', 500, '12.04.2023', 5000]
        res = self.worker.insert_order_in_db(order)
        self.assertEqual(1, res)
        query = 'SELECT * FROM orders;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.assertEqual(1, len(cur.fetchall()))

        self._truncate_table()
        order = [1, '12.04.2023', 500, 11, 5000]
        res = self.worker.insert_order_in_db(order)
        self.assertEqual(0, res)
        query = 'SELECT * FROM orders;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.assertEqual(0, len(cur.fetchall()))

    def test_update_order_in_db(self):
        """
        testing successful updating orders in DB
        """
        query = 'SELECT price_usd FROM orders WHERE order_id = %s;'
        with self.conn.cursor() as cur:
            cur.execute(query, (1,))
            old_price = cur.fetchone()

        order = [1, 1000, '12.04.2023', 5000, 1]
        res = self.worker.update_order_in_db(order)
        self.assertEqual(1, res)

        query = 'SELECT price_usd FROM orders WHERE order_id = %s;'
        with self.conn.cursor() as cur:
            cur.execute(query, (1,))
            new_price = cur.fetchone()
        self.assertNotEqual(old_price, new_price)
        self.assertEqual(1000, int(new_price[0]))

    def test_update_order_in_db_negative(self):
        """
        testing unsuccessful updating orders in DB
        - order_id not in table
        - incorrect data type
        """

        order = [1, 1000, '12.04.2023', 5000, 11]
        res = self.worker.update_order_in_db(order)
        self.assertEqual(1, res)
        query = 'SELECT price_usd FROM orders WHERE order_id = %s;'
        with self.conn.cursor() as cur:
            cur.execute(query, (11,))
            new_price = cur.fetchone()
        self.assertIsNone(new_price)

        query = 'SELECT price_usd FROM orders WHERE order_id = %s;'
        with self.conn.cursor() as cur:
            cur.execute(query, (1,))
            old_price = cur.fetchone()
        order = [1, 1000, '12.04.2023', 5000, 1]
        res = self.worker.update_order_in_db(order)
        self.assertEqual(1, res)
        query = 'SELECT price_usd FROM orders WHERE order_id = %s;'
        with self.conn.cursor() as cur:
            cur.execute(query, (1,))
            new_price = cur.fetchone()
        self.assertNotEqual(old_price, new_price)
        self.assertEqual(1000, int(new_price[0]))
