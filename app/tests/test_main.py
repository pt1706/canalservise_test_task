import unittest
from unittest.mock import patch

from main import main


class TestMain(unittest.TestCase):
    """
    testcase for testing main:
    """

    @patch('main.DBWorker')
    @patch('main.ApiHandler')
    @patch('main.CurrencyUpdater')
    @patch('builtins.print')
    def test_retrieve_currency(self,
                               mock_print,
                               mock_CurrencyUpdater,
                               mock_ApiHandler,
                               mock_DBWorker):
        """
        testcase positive outcome
        """
        mock_CurrencyUpdater().retrieve_currency.side_effect = [
            83.00, KeyError
        ]
        mock_ApiHandler().retrieve_orders.return_value = [
            ['1', '1249708', '675', '24.05.2022'],
            ['2', '1182407', '214', '13.05.2022'],
            ['3', '1120833', '610', '05.05.2022'],
        ]
        mock_DBWorker().retrieve_orders_from_db.return_value = [1249708, 4]
        mock_DBWorker().update_order_in_db.return_value = 1
        mock_DBWorker().insert_order_in_db.return_value = 1
        mock_DBWorker().delete_orders_from_db.return_value = 1

        google_cred = 'cred'
        spreadsheet_id = 'spreadsheet_id'
        with self.assertRaises(KeyError):
            main(google_cred, spreadsheet_id)

        self.assertEqual(
            2,
            mock_CurrencyUpdater().retrieve_currency.call_count
        )
        self.assertEqual(1, mock_ApiHandler().retrieve_orders.call_count)

        self.assertEqual(1, mock_DBWorker().retrieve_orders_from_db.call_count)
        self.assertEqual(1, mock_DBWorker().update_order_in_db.call_count)
        mock_DBWorker().update_order_in_db.assert_called_with(
            ['1', '675', '24.05.2022', 56025.0, '1249708']
        )

        self.assertEqual(2, mock_DBWorker().insert_order_in_db.call_count)
        mock_DBWorker().insert_order_in_db.assert_called_with(
            ['3', '1120833', '610', '05.05.2022', 50630.0]
        )

        self.assertEqual(1, mock_DBWorker().delete_orders_from_db.call_count)
        mock_DBWorker().delete_orders_from_db.assert_called_with([4])

    @patch('main.DBWorker')
    @patch('main.ApiHandler')
    @patch('main.CurrencyUpdater')
    @patch('builtins.print')
    def test_retrieve_currency_negative_api(self,
                                            mock_print,
                                            mock_CurrencyUpdater,
                                            mock_ApiHandler,
                                            mock_DBWorker):
        """
        negative testcase when Google API returns None
        """
        mock_CurrencyUpdater().retrieve_currency.side_effect = [83, KeyError]
        mock_ApiHandler().retrieve_orders.return_value = []
        mock_DBWorker().retrieve_orders_from_db.return_value = []
        mock_DBWorker().update_order_in_db.return_value = 1
        mock_DBWorker().insert_order_in_db.return_value = 1
        mock_DBWorker().delete_orders_from_db.return_value = 1

        google_cred = 'cred'
        spreadsheet_id = 'spreadsheet_id'
        with self.assertRaises(KeyError):
            main(google_cred, spreadsheet_id)

        mock_DBWorker().insert_order_in_db.assert_not_called()
        mock_DBWorker().retrieve_orders_from_db.assert_not_called()
        mock_DBWorker().update_order_in_db.assert_not_called()
        mock_DBWorker().insert_order_in_db.assert_not_called()
        mock_DBWorker().delete_orders_from_db.assert_not_called()

    @patch('main.DBWorker')
    @patch('main.ApiHandler')
    @patch('main.CurrencyUpdater')
    @patch('builtins.print')
    def test_retrieve_currency_negative_currency(self,
                                                 mock_print,
                                                 mock_CurrencyUpdater,
                                                 mock_ApiHandler,
                                                 mock_DBWorker):
        """
        negative testcase when cbr.ru returns None
        """
        mock_CurrencyUpdater().retrieve_currency.side_effect = [None, KeyError]
        mock_ApiHandler().retrieve_orders.return_value = [
            ['1', '1249708', '675', '24.05.2022'],
        ]

        mock_DBWorker().retrieve_orders_from_db.return_value = []
        mock_DBWorker().update_order_in_db.return_value = 1
        mock_DBWorker().insert_order_in_db.return_value = 1
        mock_DBWorker().delete_orders_from_db.return_value = 1

        google_cred = 'cred'
        spreadsheet_id = 'spreadsheet_id'
        with self.assertRaises(KeyError):
            main(google_cred, spreadsheet_id)

        self.assertEqual(1, mock_DBWorker().insert_order_in_db.call_count)
        mock_DBWorker().insert_order_in_db.assert_called_with(
            ['1', '1249708', '675', '24.05.2022', '???']
        )
