import inspect
from datetime import datetime, timedelta

import httplib2
from apiclient.discovery import build
import requests
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from requests import RequestException


class Logger:
    """
    Class writer of logs
    """
    @staticmethod
    def write_log(func, error=None):
        with open('log.txt', 'a') as log:
            log.write(
                f'While executing '
                f'function --- {func.upper()} --- error occurs:'
                f'\n--- {str(error).strip()} ---\n'
                f'log datatime: {datetime.now()}\n\n'
            )


class ApiHandler(Logger):
    """
    Class handler requests to google API
    """
    def __init__(self, google_cred, spreadsheet_id):
        self.CREDENTIALS_FILE = google_cred
        self.spreadsheet_id = spreadsheet_id

    def retrieve_orders(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.CREDENTIALS_FILE,
            [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        offset = 0
        res = []
        timeout = 1
        while True:
            try:
                httpAuth = credentials.authorize(httplib2.Http(
                    timeout=timeout
                ))
                service = build('sheets', 'v4', http=httpAuth)

                rows = f'{2+offset}:{102+offset}'
                values = service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=rows,
                    majorDimension='ROWS'
                ).execute().get('values', [])
                if not values:
                    break
                res += values
                offset += 100

            except TimeoutError as e:
                self.write_log(inspect.stack()[0][3], e)
                if timeout > 2:
                    return None
                timeout += 0.5

            except HttpError as e:
                self.write_log(inspect.stack()[0][3], e)
                return res
        return res


class CurrencyUpdater(Logger):
    """
    Class handler requests to cbr.ru
    """

    def retrieve_currency(self):
        """
        method return currency rate or None if not available
        """
        offset = 0
        timeout = 0.1
        error = 0
        msg = 'Status codes of responses'
        while True:
            try:
                date = (
                    datetime.today() - timedelta(days=offset)
                ).strftime('%d/%m/%Y')
                url = f'https://www.cbr.ru/scripts/XML_dynamic.asp?' \
                      f'date_req1={date}&date_req2={date}&VAL_NM_RQ=R01235'
                res_request = requests.get(url, timeout=timeout)
                if str(res_request.status_code)[0] in ['4', '5']:
                    if error > 4:
                        msg += ' ' + str(res_request.status_code)
                        self.write_log(inspect.stack()[0][3], msg)
                        return None
                    msg += ' ' + str(res_request.status_code)
                    error += 1
                    continue
                if res_request.text.find('<Value>') != -1:
                    break
                offset += 1

            except RequestException as e:
                self.write_log(inspect.stack()[0][3], e)
                if timeout > 0.3:
                    return None
                timeout += 0.1
        res_request = res_request.text.split('<Value>')[1].split(
            '</Value>'
        )[0].replace(',', '.')
        return float(res_request)
