from datetime import datetime, timedelta
from django.test import TestCase
from corehq.apps.commtrack.models import SupplyPointCase, StockState
from corehq.apps.commtrack.tests.util import bootstrap_domain as initial_bootstrap
from corehq.apps.locations.models import Location, SQLLocation
from corehq.apps.products.models import SQLProduct, Product
from custom.ilsgateway.api import ILSGatewayAPI
from custom.ilsgateway.models import ReportRun, ILSGatewayConfig, ProductAvailabilityData, OrganizationSummary, \
    GroupSummary
from custom.ilsgateway.tanzania.warehouse_updater import populate_report_data
from custom.ilsgateway.tests import MockEndpoint
from casexml.apps.stock.models import StockReport, StockTransaction

TEST_DOMAIN = 'report-runner-test'


def create_stock_report(location, product, stock_on_hand):
    report = StockReport(
        form_id='test',
        date=datetime.now(),
        type='balance',
        domain=TEST_DOMAIN
    )
    report.save()
    stock_transaction = StockTransaction(
        case_id=location.supply_point_id,
        product_id=product.product_id,
        sql_product=product,
        section_id='stock',
        type='stockonhand',
        stock_on_hand=stock_on_hand,
        report=report
    )
    stock_transaction.save()


class ReportRunnerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        initial_bootstrap(TEST_DOMAIN)
        endpoint = MockEndpoint('http://test-api.com/', 'dummy', 'dummy')
        config = ILSGatewayConfig(enabled=True, domain=TEST_DOMAIN, all_stock_data=True)
        config.save()
        api_object = ILSGatewayAPI(TEST_DOMAIN, endpoint)
        api_object.prepare_commtrack_config()

        district = Location(domain=TEST_DOMAIN, name='Test district', location_type='DISTRICT')
        district.save()

        for i in xrange(20):
            facility_name = "Test facility%d" % i
            facility = Location(parent=district, domain=TEST_DOMAIN, name=facility_name, location_type='FACILITY')
            facility.save()

            SupplyPointCase.create_from_location(TEST_DOMAIN, facility)
            facility.save()

        product_name = "Test product1"
        product = Product(domain=TEST_DOMAIN, name=product_name)
        product.save()

    def tearDown(self):
        all_stock_transactions = StockTransaction.objects.all()
        for stock_transaction in all_stock_transactions:
            stock_transaction.delete()

        all_stock_states = StockState.objects.all()
        for stock_state in all_stock_states:
            stock_state.delete()

        all_product_availability = ProductAvailabilityData.objects.all()
        for product_availability in all_product_availability:
            product_availability.delete()

        all_organization_summary = OrganizationSummary.objects.all()
        for organization_summary in all_organization_summary:
            organization_summary.delete()

        all_group_summary = GroupSummary.objects.all()
        for group_summary in all_group_summary:
            group_summary.delete()

    def test_product_availability(self):
        locations = SQLLocation.objects.filter(domain=TEST_DOMAIN)
        self.assertEqual(20, locations.filter(location_type__name='FACILITY', domain=TEST_DOMAIN).count())
        self.assertEqual(1, locations.filter(location_type__name='DISTRICT', domain=TEST_DOMAIN).count())
        quantities = []
        product = SQLProduct.objects.filter(domain=TEST_DOMAIN)[0]
        for i in xrange(10):
            quantities.append(0)  # stockout
            quantities.append(5)  # not stockout
        for idx, location in enumerate(locations.filter(location_type__name='FACILITY', domain=TEST_DOMAIN)):
            create_stock_report(location, product, quantities[idx])
        start_date = datetime.utcnow().replace(day=1)
        end_date = datetime.utcnow()
        run = ReportRun.objects.create(start=start_date, end=end_date,
                                       start_run=datetime.utcnow(), domain=TEST_DOMAIN)
        populate_report_data(start_date, end_date, TEST_DOMAIN, run)
        district = locations.filter(location_type__name='DISTRICT')[0]
        district_product_availabilty = ProductAvailabilityData.objects.filter(supply_point=district.location_id)[0]

        self.assertEqual(10, district_product_availabilty.without_stock)
        self.assertEqual(10, district_product_availabilty.with_stock)
        self.assertEqual(20, district_product_availabilty.total)
        self.assertEqual(product.product_id, district_product_availabilty.product)

    def test_product_availability2(self):
        locations = SQLLocation.objects.filter(domain=TEST_DOMAIN)
        self.assertEqual(20, locations.filter(location_type__name='FACILITY', domain=TEST_DOMAIN).count())
        self.assertEqual(1, locations.filter(location_type__name='DISTRICT', domain=TEST_DOMAIN).count())
        quantities = []
        product = SQLProduct.objects.filter(domain=TEST_DOMAIN)[0]
        for i in xrange(10):
            quantities.append((5, 0))  # stockout
            quantities.append((0, 5))  # not stockout
        for idx, location in enumerate(locations.filter(location_type__name='FACILITY', domain=TEST_DOMAIN)):
            create_stock_report(location, product, quantities[idx][0])
            create_stock_report(location, product, quantities[idx][1])

        start_date = datetime.utcnow().replace(day=1)
        end_date = datetime.utcnow()
        run = ReportRun.objects.create(start=start_date, end=end_date,
                                       start_run=datetime.utcnow(), domain=TEST_DOMAIN)
        populate_report_data(start_date, end_date, TEST_DOMAIN, run)
        district = locations.filter(location_type__name='DISTRICT')[0]
        district_product_availabilty = ProductAvailabilityData.objects.filter(supply_point=district.location_id)[0]

        self.assertEqual(10, district_product_availabilty.without_stock)
        self.assertEqual(10, district_product_availabilty.with_stock)
        self.assertEqual(20, district_product_availabilty.total)
        self.assertEqual(product.product_id, district_product_availabilty.product)

