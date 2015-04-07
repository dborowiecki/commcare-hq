import json
import os
from datetime import timedelta, datetime
import itertools
import math
from corehq.apps.commtrack.models import StockState, CommtrackConfig, ConsumptionConfig
from corehq.apps.locations.models import SQLLocation
from corehq.apps.products.models import SQLProduct
from dimagi.utils.dates import delta_secs, force_to_datetime
from django.test import TestCase
from casexml.apps.stock.models import StockTransaction
from custom.ewsghana.api import EWSApi, Location
from custom.ewsghana.models import EWSGhanaConfig
from custom.ewsghana.tests.mock_endpoint import MockEndpoint
from custom.ewsghana.tests import TEST_DOMAIN
from corehq.apps.commtrack.tests.util import bootstrap_domain as initial_bootstrap
from custom.ewsghana.api import Product
from custom.logistics.tasks import sync_stock_transactions, stock_data_task
from custom.ewsghana.api import StockTransaction as EWSTransaction


def compute_consumption_in_logistics_way(txs):
    """
    Calculate daily consumption through the following algorithm:

    Consider each non-stockout SOH report to be the start of a period.
    We iterate through the stock transactions following it until we reach another SOH.
    If it's a stockout, we drop the period from the calculation.

    We keep track of the total receipts in each period and add them to the start quantity.
    The total quantity consumed is: (Start SOH Quantity + SUM(receipts during period) - End SOH Quantity)

    We add the quantity consumed and the length of the period to the running count,
    then at the end divide one by the other.

    This algorithm effectively deals with cases where a SOH report immediately follows a receipt.
    """

    total_time = timedelta(0)
    total_consumption = 0

    period_receipts = 0
    end_transaction = None
    periods = []
    for t in reversed(txs):
        date = force_to_datetime(t.date)
        if t.ending_balance == 0:
            # Previous period ended in stockout -- pass on this period
            end_transaction = None
            period_receipts = 0
            continue
        if t.report_type == 'Stock on Hand':
            if end_transaction:
                # End of a period.
                if t.ending_balance + period_receipts >= end_transaction.ending_balance:
                    # if this check fails it's an anomalous data point
                    # (finished with higher stock than possible)

                    # Add the period stats to the running count.
                    # But first scale them if they fall within the cutoff window
                    period_time = (force_to_datetime(end_transaction.date) - date)
                    period_consumption = t.ending_balance + period_receipts - end_transaction.ending_balance
                    if datetime.min < date:
                        scaling_factor = 1
                    else:
                        scaling_factor = max(0, delta_secs(force_to_datetime(end_transaction.date)
                                                           - datetime.min / delta_secs(period_time)))

                    total_time += timedelta(seconds=scaling_factor * delta_secs(period_time))
                    total_consumption += scaling_factor * period_consumption
                    periods.append((date, end_transaction.date, total_consumption))
                else:
                    print t, end_transaction, period_receipts

            if date < datetime.min:
                break
            else:
                # Start a new period.
                end_transaction = t
                period_receipts = 0

        elif t.report_type == 'Stock Received':
            # Receipt.
            if end_transaction:
                # Mid-period receipt, so we care about it.
                period_receipts += t.quantity
    days = total_time.days
    if days < 2:
        return None
    return round(abs((float(total_consumption) / delta_secs(total_time)) * 60*60*24), 2)


class TestStockTransactionSync(TestCase):

    @classmethod
    def setUpClass(cls):
        endpoint = MockEndpoint('http://test-api.com/', 'dummy', 'dummy')
        api_object = EWSApi(TEST_DOMAIN, endpoint)
        datapath = os.path.join(os.path.dirname(__file__), 'data')
        initial_bootstrap(TEST_DOMAIN)
        config = CommtrackConfig.for_domain(TEST_DOMAIN)
        config.consumption_config = ConsumptionConfig(min_transactions=2, min_window=10, optimal_window=9999)
        config.save()
        api_object.prepare_commtrack_config()
        with open(os.path.join(datapath, 'sample_products.json')) as f:
            products = [Product(product) for product in json.loads(f.read())]

        with open(os.path.join(datapath, 'sample_locations.json')) as f:
            locations = [Location(location) for location in json.loads(f.read())]

        for product in products:
            api_object.product_sync(product)

        for location in locations:
            api_object.location_sync(location)

    def get_monthly_consumption(self, code, location):
        product = SQLProduct.objects.get(domain=TEST_DOMAIN, code=code)
        product_stock = StockState.objects.get(case_id=location.supply_point_id, product_id=product.product_id)
        monthly_consumption = product_stock.get_monthly_consumption()
        return math.ceil(monthly_consumption) if monthly_consumption else 0

    def test_stock_transaction_sync(self):

        apis = (
            ('stock_transaction', sync_stock_transactions),
        )
        endpoint = MockEndpoint('http://test-api.com/', 'dummy', 'dummy')
        stock_data_task(TEST_DOMAIN, endpoint, apis, EWSGhanaConfig(all_stock_data=False), test_facilities=[654])
        self.assertGreater(StockTransaction.objects.all().count(), 0)
        datapath = os.path.join(os.path.dirname(__file__), 'data')
        with open(os.path.join(datapath, 'sample_stocktransactions.json')) as f:
            transactions = [EWSTransaction(transaction) for transaction in json.loads(f.read())]

        tx_dict = {}
        for tx in transactions:
            if tx.product in tx_dict:
                tx_dict[tx.product].append(tx)
            else:
                tx_dict[tx.product] = [tx]
        results_map = {}
        for k, v in tx_dict.iteritems():
            daily_consumption = compute_consumption_in_logistics_way(v)
            results_map[k] = math.ceil(daily_consumption * 30) if daily_consumption else 0

        self.assertEqual(159, results_map['ali'])
        self.assertEqual(1330, results_map['alk'])
        self.assertEqual(12, results_map['aai'])
        self.assertEqual(60, results_map['aak'])
        self.assertEqual(22, results_map['co'])
        self.assertEqual(16, results_map['dp'])
        self.assertEqual(344, results_map['rd'])
        self.assertEqual(7, results_map['mc'])
        self.assertEqual(3, results_map['mg'])
        self.assertEqual(0, results_map['ml'])
        self.assertEqual(2, results_map['ng'])
        self.assertEqual(2, results_map['sp'])

        location = SQLLocation.objects.get(domain=TEST_DOMAIN, site_code='crms')

        self.assertEqual(results_map['ali'], self.get_monthly_consumption('ali', location))
        self.assertEqual(results_map['alk'], self.get_monthly_consumption('alk', location))
        self.assertEqual(results_map['aai'], self.get_monthly_consumption('aai', location))
        self.assertEqual(results_map['aak'], self.get_monthly_consumption('aak', location))
        self.assertEqual(results_map['co'], self.get_monthly_consumption('co', location))
        self.assertEqual(results_map['dp'], self.get_monthly_consumption('dp', location))
        self.assertEqual(results_map['rd'], self.get_monthly_consumption('rd', location))
        self.assertEqual(results_map['mc'], self.get_monthly_consumption('mc', location))
        self.assertEqual(results_map['mg'], self.get_monthly_consumption('mg', location))
        self.assertEqual(results_map['ml'], self.get_monthly_consumption('ml', location))
        self.assertEqual(results_map['ng'], self.get_monthly_consumption('ng', location))
        self.assertEqual(results_map['sp'], self.get_monthly_consumption('sp', location))