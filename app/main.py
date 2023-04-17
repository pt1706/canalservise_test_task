import inspect
import os
import time

from db_worker import DBWorker
from http_worker import ApiHandler, CurrencyUpdater, Logger


def main(google_cred, spreadsheet_id, host='db'):
    while True:
        print('Start updating...')
        start = time.time()
        currency = CurrencyUpdater().retrieve_currency()
        orders_in_table = ApiHandler(
            google_cred, spreadsheet_id
        ).retrieve_orders()
        if not orders_in_table:
            msg = f'End updating due to error. ' \
                  f'Time execution ---{time.time() - start:0.3f} c---\n'
            Logger.write_log(inspect.stack()[0][3], msg)
            print(msg)
            continue
        db_worker = DBWorker(host=host)
        order_in_db = db_worker.retrieve_orders_from_db()
        updated = []
        added = []
        for order in orders_in_table:
            if int(order[1]) in order_in_db:
                args = [order[0], order[2], order[3],
                        int(order[2]) * currency if currency else '???',
                        order[1]]
                db_worker.update_order_in_db(args)
                updated.append(int(order[1]))
            else:
                args = order + [
                    int(order[2]) * currency if currency else '???'
                ]
                db_worker.insert_order_in_db(args)
                added.append(order[1])

        deleted = list(set(order_in_db) - set(updated))
        if deleted:
            db_worker.delete_orders_from_db(deleted)

        print(f'deleted -> {deleted}')
        print(f'updated -> {updated}')
        print(f'added -> {added}')
        print(
            f'Successfully updated. '
            f'Time execution ---{time.time() - start:0.3f} c---\n'
        )


if __name__ == '__main__':
    google_cred = os.environ.get('google_cred')
    spreadsheet_id = os.environ.get('spreadsheet_id')
    host = os.environ.get('host', 'db')
    main(google_cred, spreadsheet_id, host)
