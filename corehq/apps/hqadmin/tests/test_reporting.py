import types
from datetime import datetime, date

import mock
from dateutil.relativedelta import relativedelta
from django.test import TestCase

from corehq.apps.accounting.models import Subscriber, Subscription, BillingAccount, DefaultProductPlan, \
    SoftwarePlanEdition
from corehq.apps.app_manager.models import Application, Module, Form
from corehq.apps.domain.models import Domain, Deployment
from corehq.apps.es import DomainES
from corehq.apps.es.sms import SMSES
from corehq.apps.hqadmin.reporting.exceptions import IntervalNotFoundException
from corehq.apps.hqadmin.reporting.reports import add_params_to_query, get_data_point, format_return_data, \
    add_blank_data, daterange, get_timestep, get_project_spaces, get_mobile_users, get_sms_query, \
    get_active_countries_stats_data, domains_matching_plan, plans_on_date, get_subscription_stats_data, \
    get_active_domain_stats_data, get_active_users_data, get_active_dimagi_owned_gateway_projects, \
    get_countries_stats_data, get_active_supply_points_data, get_total_clients_data, get_mobile_workers_data, \
    get_commconnect_domain_stats_data, get_all_subscriptions_stats_data, get_domain_stats_data, \
    commtrack_form_submissions, get_stock_transaction_stats_data, get_active_cases_stats, get_case_stats, \
    get_form_stats, get_user_stats, get_users_all_stats, get_user_ids, get_submitted_users, get_case_owner_filters, \
    get_unique_locations_data, get_location_type_data
from corehq.apps.hqadmin.tests.utils import TestElasticsearchReportMixin
from corehq.apps.locations.models import SQLLocation
from corehq.apps.sms.models import SMS, SQLMobileBackend
from corehq.apps.users.models import CommCareUser
from corehq.elastic import get_es_new, send_to_elasticsearch, ES_MAX_CLAUSE_COUNT
from corehq.pillows.mappings.domain_mapping import DOMAIN_INDEX_INFO
from corehq.pillows.mappings.sms_mapping import SMS_INDEX_INFO
from corehq.pillows.mappings.user_mapping import USER_INDEX, USER_INDEX_INFO
from corehq.pillows.mappings.xform_mapping import XFORM_INDEX_INFO
from corehq.pillows.xform import transform_xform_for_elasticsearch
from corehq.util.dates import get_timestamp_millis
from corehq.util.elastic import ensure_index_deleted
from couchforms.models import XFormInstance
from dimagi.utils.dates import DateSpan
from pillowtop.es_utils import initialize_index_and_mapping


class TestReportingFunctions(TestCase, TestElasticsearchReportMixin):
    now = datetime(year=2019, month=9, day=13)
    then = datetime(year=2019, month=9, day=10)
    datespan = DateSpan(then, now)

    @classmethod
    def setUpClass(cls):
        super(TestReportingFunctions, cls).setUpClass()
        cls.create_setup()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_class()
        super(TestReportingFunctions, cls).tearDownClass()

    def test_adding_params_to_query(self):
        query = DomainES()

        result = add_params_to_query(query, {'name': 't3st'})
        terms = [term.get('terms') for term in result.filters if term.get('terms')]
        param_in_query = next(param for param in terms if param.get('name') == 't3st')

        self.assertIsNotNone(param_in_query)

    def test_adding_search_param_to_query(self):
        query = DomainES()

        result = add_params_to_query(query, {'search': 'i_shall_not_be_in_query'})
        terms = [term.get('terms', {}).get('search') for term in result.filters if term.get('terms')]

        self.assertEqual(len(terms), 0)

    def test_get_data_point(self):
        now = datetime.now()
        count = 10

        actual = get_data_point(count, now)
        expected = {'count': count, 'time': get_timestamp_millis(now)}

        self.assertDictEqual(expected, actual)

    def test_format_return_data(self):
        now = datetime(year=2019, month=9, day=14)
        datespan = DateSpan(self.then, now)

        expected = {
            'histo_data': {'All Domains': now},
            'initial_values': {"All Domains": 0},
            'startdate': datespan.startdate_key_utc,
            'enddate': datespan.enddate_key_utc,

        }

        actual = format_return_data(now, 0, datespan)

        self.assertDictEqual(expected, actual)

    def test_add_blank_data(self):
        now = datetime(year=2019, month=9, day=14)

        start = {'count': 0, 'time': get_timestamp_millis(self.then)}
        end = {'count': 0, 'time': get_timestamp_millis(now)}
        expected = [start, end]

        actual = add_blank_data(None, start=self.then, end=now)

        self.assertEqual(expected, actual)

    def test_get_timestep(self):
        expected = [
            relativedelta(days=1),
            relativedelta(weeks=1),
            relativedelta(months=1),
            relativedelta(years=1)
        ]
        actual = [
            get_timestep('day'),
            get_timestep('week'),
            get_timestep('month'),
            get_timestep('year'),
        ]

        self.assertEqual(expected, actual)

    def test_get_timestep_not_found_exception(self):
        with self.assertRaises(IntervalNotFoundException):
            get_timestep('light_year')

    def test_daterange(self):
        now = datetime(year=2019, month=9, day=14)
        
        interval = 'day'
        expected = [self.then+relativedelta(days=n) for n in range(0, 14-10)]
        expected.append(now)

        actual = daterange(interval, self.then, now)

        self.assertIsInstance(actual, types.GeneratorType)
        self.assertEqual(expected, list(actual))

    def test_get_project_spaces(self):
        # TODO: check if facest default empty list would be better than None, that causes exception throw
        actual = get_project_spaces(facets={'search': [self.domain_name]})

        self.assertIn(self.domain_name, actual)

    def test_get_mobile_users(self):
        actual = get_mobile_users([self.domain_name])

        self.assertIn(self.user.user_id, actual)

    def test_get_sms_query(self):
        now = datetime(year=2019, month=9, day=14)


        # TODO: check if this method should return
        # Now it returns query with size 0 so no SMSes are returned
        actual_query = get_sms_query(begin=self.then, end=now, facet_name='domains',
                                     facet_terms='domain', domains=[self.domain_name])

        result = actual_query.run().aggregations.domains.keys

        self.assertIsInstance(actual_query, SMSES)
        self.assertIn(self.domain_name, result)

    def test_get_active_countries_stats_data(self):
        now = datetime(year=2019, month=9, day=14)
        datespan = DateSpan(self.then, now)

        result = get_active_countries_stats_data([self.domain.name], datespan, 'day')

        self.assertEqual(len(result['histo_data']['All Domains']), 3)

    def test_domains_matching_plan(self):
        now = datetime(year=2019, month=9, day=14)

        result = domains_matching_plan(SoftwarePlanEdition.ADVANCED, self.then, now)

        self.assertIn(self.domain_name, result)

    def test_plans_on_date(self):
        date = datetime(year=2019, month=9, day=12)

        result = plans_on_date(SoftwarePlanEdition.ADVANCED, date)

        self.assertIn(self.domain_name, result)

    def test_plans_on_date_negative(self):
        date = datetime(year=2019, month=9, day=19)

        result = plans_on_date(SoftwarePlanEdition.ADVANCED, date)

        self.assertNotIn(self.domain_name, result)

    def test_get_subscription_stats_data(self):
        now = datetime(year=2019, month=9, day=15)
        then = datetime(year=2019, month=9, day=14)
        datespan = DateSpan(then, now)

        result = get_subscription_stats_data([self.domain_name], datespan=datespan, interval='day',
                                             software_plan_edition=SoftwarePlanEdition.ADVANCED)

        self.assertEqual(result[0]['count'], 1)
        self.assertEqual(result[1]['count'], 0)

    def test_get_active_domain_stats_data(self):
        now = datetime(year=2019, month=9, day=16)
        then = datetime(year=2019, month=9, day=14)
        datespan = DateSpan(then, now)

        result = get_active_domain_stats_data(domains=[self.domain.name],datespan=datespan,
                                              interval='day', software_plan_edition=SoftwarePlanEdition.ADVANCED)

        self.assertEqual(len(result['histo_data']['All Domains']), 3)

    def test_get_active_users_data(self):
        result = get_active_users_data(domains=[self.domain.name],datespan=self.datespan,interval='day',include_forms=True)

        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_active_users_data_negative(self):
        now = datetime(year=2019, month=9, day=11)
        datespan = DateSpan(self.then, now)

        result = get_active_users_data(domains=[self.domain.name], datespan=datespan,
                                       interval='day', include_forms=True)

        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 0)

    @mock.patch.object(SQLMobileBackend, 'get_global_backend_ids', return_value=['super_cool_id'])
    def test_get_active_dimagi_owned_gateway_projects(self, mobile_backend_mock):
        result = get_active_dimagi_owned_gateway_projects(
            domains=[self.domain.name], datespan=self.datespan, interval='day')

        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_countries_stats_data(self):
        result = get_countries_stats_data([self.domain_name], self.datespan, 'day')
        actual = len(self.domain.deployment.countries)
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], actual)

    def test_get_active_supply_points_data(self):
        result = get_active_supply_points_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_total_clients_data(self):
        result = get_total_clients_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_mobile_workers_data(self):
        result = get_mobile_workers_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_commconnect_domain_stats_data(self):
        result = get_commconnect_domain_stats_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_all_subscriptions_stats_data(self):
        result = get_all_subscriptions_stats_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['Advanced'][0]['count'], 1)

    def test_get_domain_stats_data(self):
        result = get_domain_stats_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_commtrack_form_submissions(self):
        result = commtrack_form_submissions([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_stock_transaction_stats_data(self):
        result = get_stock_transaction_stats_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 0)
        self.assertEqual(result['histo_data']['All Domains'][1]['count'], 1)

    def test_get_form_stats(self):
        result = get_form_stats([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data'][self.domain_name][0]['count'], 1)

    def test_get_user_stats_too_many_domains(self):
        result = get_user_stats([self.domain_name for _ in range(0, ES_MAX_CLAUSE_COUNT)],
                                self.datespan, 'day')
        key = 'All Domains (NOT applying filters. > {} projects)'.format(ES_MAX_CLAUSE_COUNT)
        self.assertEqual(result['histo_data'][key][0]['count'], 1)

    #
    # def test_get_case_stats(self):
    #     # needs investigation, probably fails because there is no
    #     # "case": [
    #     #         {"term": {"doc_type": "CommCareCase"}},
    #     #     ],
    #     # in ADD_TO_ES_FILTER dict in elastic.py
    #     result = get_case_stats([self.domain_name], self.datespan, 'day')
    #     print(result)
    #     self.assertEqual(result['histo_data'][self.domain_name][0]['count'], 1)

    def test_get_users_all_stats(self):
        result = get_users_all_stats([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)

    def test_get_user_ids(self):
        result = get_user_ids(True, [self.domain_name])
        self.assertIn(self.user.user_id, result)

    def test_get_case_owner_filters(self):
        result = get_case_owner_filters([self.domain_name])
        actual = result['terms']['owner_id']
        expected = [self.user.user_id, self.group._id]
        self.assertListEqual(expected, actual)

    def test_get_unique_locations_data(self):
        result = get_unique_locations_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data'][self.domain_name][0]['count'], 1)

    def test_get_location_type_data(self):
        result = get_location_type_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data'][self.domain_name][0]['count'], 1)

    def test_get_stats_data(self):
        result = get_location_type_data([self.domain_name], self.datespan, 'day')
        self.assertEqual(result['histo_data'][self.domain_name][0]['count'], 1)

    # def test_get_submitted_users(self):
    #     result = get_submitted_users([self.domain_name])
    #     self.assertEqual(result['histo_data']['All Domains'][0]['count'], 1)
