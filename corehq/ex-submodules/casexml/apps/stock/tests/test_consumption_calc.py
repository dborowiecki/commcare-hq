from django.test import SimpleTestCase
from casexml.apps.stock.tests.mock_consumption import mock_consumption as consumption, mock_transaction as _tx


class ConsumptionCalcTest(SimpleTestCase):

    def test_one_period(self):
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 5),
                _tx('stockonhand', 25, 0),
            ], 60), 0.)
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 5),
                _tx('receipts', 10, 0),
                _tx('stockonhand', 35, 0),
            ], 60), 0.)
        # 15 / 5 = 3
        """
            In EWS this period should be dropped and None should be returned
            because clause (start period soh) + (receipts in period) > (end period soh) doesn't pass.
            (25 + 10 > 40)
            I think that similar situation isn't possible in HQ
            because commtrack is inferring additional receipt so in this case
            before soh 40 receipt 20 should be added. With inferred transactions clause above will be always correct.
            _tx('stockonhand', 25, 5),
            _tx('receipts', 10, 0),
            _tx('consumption', 15, 0),
            _tx('receipts', 20, 0),  # inferred
            _tx('stockonhand', 40, 0)
            Then obviously 25 + 30 > 40
        """
        self.assertAlmostEqual(
            consumption(
                [
                    _tx('stockonhand', 25, 5),
                    _tx('receipts', 10, 0),
                    _tx('consumption', 15, 0),
                    _tx('stockonhand', 40, 0)
                ], 60
            ), 3.
        )
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 5),
                _tx('consumption', 15, 0),
                _tx('stockonhand', 10, 0),
            ], 60), 3.)
        # 27 / 5 = 5.4
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 5),
                _tx('receipts', 12, 3),
                _tx('consumption', 27, 0),
                _tx('stockonhand', 10, 0),
            ], 60), 5.4)
        # (6 + 21) / 5 = 5.4
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 5),
                _tx('consumption', 6, 3),
                _tx('receipts', 12, 3),
                _tx('consumption', 21, 0),
                _tx('stockonhand', 10, 0),
            ], 60), 5.4)

    def test_multiple_periods(self):
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 15),

                _tx('consumption', 4, 12),
                _tx('receipts', 12, 12),
                _tx('stockonhand', 33, 12),

                _tx('consumption', 30, 7),
                _tx('receipts', 3, 7),
                _tx('stockonhand', 6, 7),

                _tx('consumption', 10, 0),
                _tx('receipts', 14, 0),
                _tx('stockonhand', 10, 0),
            ], 60), 44/15.)

    def test_excluded_period(self):
        self.assertAlmostEqual(consumption([
                _tx('stockonhand', 25, 15),

                _tx('consumption', 4, 12),
                _tx('receipts', 12, 12),
                _tx('stockonhand', 33, 12),

                _tx('consumption', 36, 7),
                _tx('receipts', 3, 7),
                _tx('stockout', 0, 7), # stockout

                _tx('consumption', 5, 5),
                _tx('receipts', 25, 5), # restock, consumption days 12-5 ignored
                _tx('stockonhand', 20, 5),

                _tx('consumption', 10, 0),
                _tx('receipts', 14, 0),
                _tx('stockonhand', 24, 0),
            ], 60), 1.75)

    def test_prorated_period(self):
        tx_past_window = [
            _tx('stockonhand', 200, 65),

            _tx('consumption', 100, 50),
            _tx('receipts', 50, 50),
            _tx('stockonhand', 150, 50),
            
            _tx('consumption', 20, 0),
            _tx('receipts', 30, 0),
            _tx('stockonhand', 160, 0),
        ]
        self.assertAlmostEqual(consumption(tx_past_window, 60), 1.44444444)
        self.assertAlmostEqual(consumption(tx_past_window, 55), 0.96969696)

    def test_thresholds(self):
        tx = [
            _tx('stockonhand', 25, 15),

            _tx('consumption', 4, 12),
            _tx('receipts', 12, 12),
            _tx('stockonhand', 33, 12),

            _tx('consumption', 30, 7),
            _tx('receipts', 3, 7),
            _tx('stockonhand', 6, 7),

            _tx('consumption', 10, 0),
            _tx('receipts', 14, 0),
            _tx('stockonhand', 10, 0),
        ]
        self.assertEqual(consumption(tx, 60, {'min_periods': 4}), None)
        self.assertAlmostEqual(consumption(tx, 60, {'min_periods': 3}), 44/15.)
        self.assertEqual(consumption(tx, 60, {'min_window': 16}), None)
        self.assertAlmostEqual(consumption(tx, 60, {'min_window': 15}), 44/15.)
