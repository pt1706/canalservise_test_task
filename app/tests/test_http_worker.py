import unittest
from unittest.mock import patch, Mock

from freezegun import freeze_time

import responses

from http_worker import CurrencyUpdater, ApiHandler


class TestCurrencyUpdater(unittest.TestCase):
    """
    testcase for testing CurrencyUpdater:
    if cbr.ru does not provide any answers return None
    if cbr.ru provides currency return value
    """

    @responses.activate
    @freeze_time("2023-04-08")
    def test_retrieve_currency(self):
        """
        testcase positive outcome
        """
        url_no_currency = 'https://www.cbr.ru/scripts/XML_dynamic.asp?'\
                          'date_req1=08/04/2023&date_req2=08/04/2023&'\
                          'VAL_NM_RQ=R01235'
        res_no_currency = '</ValCurs>'

        responses.add(
            responses.GET,
            url=url_no_currency,
            body=res_no_currency
        )

        res = CurrencyUpdater().retrieve_currency()
        self.assertEqual(None, res)

        url_with_currency = 'https://www.cbr.ru/scripts/XML_dynamic.asp?'\
                            'date_req1=07/04/2023&date_req2=07/04/2023&'\
                            'VAL_NM_RQ=R01235'
        res_with_currency = '<Value>79,0</Value>'
        responses.add(
            responses.GET,
            url=url_with_currency,
            body=res_with_currency
        )
        res = CurrencyUpdater().retrieve_currency()
        self.assertEqual(79, res)

    @responses.activate
    @freeze_time("2023-04-08")
    def test_retrieve_currency_negative(self):
        """
        testcase positive outcome
        """
        url_no_currency = 'https://www.cbr.ru/scripts/XML_dynamic.asp?'\
                          'date_req1=08/04/2023&date_req2=08/04/2023'\
                          '&VAL_NM_RQ=R01235'
        res_no_currency = '404 Not Found'

        responses.add(
            responses.GET,
            url=url_no_currency,
            body=res_no_currency,
            status=404
        )

        res = CurrencyUpdater().retrieve_currency()
        self.assertEqual(None, res)


class TestApiHandler(unittest.TestCase):
    """
    testcase for testing google sheets API:
    """

    def setUp(self):
        self.google_cred = 'cred'
        self.spreadsheet_id = 'spreadsheet_id'

    @patch('http_worker.build')
    @patch('http_worker.ServiceAccountCredentials')
    def test_retrieve_orders_one_request(self,
                                         mock_ServiceAccountCredentials,
                                         mock_build):
        """
        testing retrieving rows requires one request
        """

        mock_build.return_value.spreadsheets.return_value.\
            values.return_value.get.return_value.\
            execute.return_value = {'values': []}
        res = ApiHandler(
            self.google_cred, self.spreadsheet_id
        ).retrieve_orders()
        self.assertEqual([], res)
        self.assertIn(
            self.google_cred,
            *mock_ServiceAccountCredentials.from_json_keyfile_name.call_args
        )

    @patch('http_worker.build')
    @patch('http_worker.ServiceAccountCredentials')
    def test_retrieve_orders_some_request(self,
                                          mock_ServiceAccountCredentials,
                                          mock_build):
        """
        testing retrieving rows requires more than one request
        """

        mock_build_res = Mock()
        mock_build_res.side_effect = [
            {'values': [1, 2, 3]},
            {'values': [4, 5, 6]},
            {'values': []}
        ]
        mock_build.return_value.spreadsheets.return_value.\
            values.return_value.get.return_value.\
            execute = mock_build_res
        res = ApiHandler(
            self.google_cred, self.spreadsheet_id
        ).retrieve_orders()
        self.assertEqual([1, 2, 3, 4, 5, 6], res)

    @patch('http_worker.build')
    @patch('http_worker.ServiceAccountCredentials')
    def test_retrieve_orders_negative(self,
                                      mock_ServiceAccountCredentials,
                                      mock_build):
        """
        testing raising exception while retrieving rows
        """

        mock_build_res = Mock()
        mock_build_res.side_effect = TimeoutError
        mock_build.return_value.spreadsheets.\
            return_value.values.return_value.get.\
            return_value.execute = mock_build_res
        res = ApiHandler(
            self.google_cred, self.spreadsheet_id
        ).retrieve_orders()
        self.assertEqual(None, res)
