from unittest import TestCase

import redis
from django.test import SimpleTestCase, TransactionTestCase

import corehq
from corehq.apps.es import GroupES
from corehq.apps.hqadmin.service_checks import check_redis, check_kafka, check_elasticsearch, check_postgres, \
    check_couch, run_checks
from corehq.elastic import get_es_new, send_to_elasticsearch
from corehq.form_processor.tests.utils import run_with_all_backends
from unittest.mock import patch, MagicMock, Mock

from corehq.pillows.mappings.group_mapping import GROUP_INDEX_INFO
from corehq.util.elastic import ensure_index_deleted
from pillowtop.es_utils import initialize_index_and_mapping

es = get_es_new()
initialize_index_and_mapping(es, GROUP_INDEX_INFO)


class CheckMock:
    def set(self, *args, **kwargs):
        return True


class KafkaMock:
    def __init__(self, number_of_brokers=0, number_of_topics=0):
        self.cluster = MagicMock()
        self.cluster.brokers.return_value = [i for i in range(number_of_brokers)]
        self.cluster.topics.return_value = [i for i in range(number_of_topics)]


def mocked_es_send(index_name, doc, **kwargs):
    if kwargs.get('delete', False):
        ensure_index_deleted(index_name)
    else:
        send_to_elasticsearch(index_name, doc, **kwargs)


def mocked_es_refresh(index):
    es.indices.refresh(index)


class TestServices(TransactionTestCase):

    databases = {'default'}
    @classmethod
    def setUpClass(cls):
        super(TestServices, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(TestServices, cls).tearDownClass()

    @patch('corehq.apps.hqadmin.service_checks.cache.caches')
    @run_with_all_backends
    def test_redis_check(self, cache_mock):
        memory = 10
        cache_mock.return_value = {
            'redis': CheckMock()
        }

        redis_api_mock = Mock()
        redis_api_mock.info.return_value = {
                'used_memory_human': 10
            }

        with patch.object(
                redis.StrictRedis,
                'from_url',
                return_value=redis_api_mock
        ) as redis_mock:
            x = check_redis()
            self.assertEqual(x.msg, 'Redis is up and using {} memory'.format(memory))

    @patch('django.conf.settings.CACHES')
    @run_with_all_backends
    def test_non_configured_redis_check(self, cache_mock):
        cache_mock.return_value = ['no', 'redis', 'here']
        x = check_redis()
        self.assertEqual(x.msg, 'Redis is not configured on this system!')

    @run_with_all_backends
    @patch('corehq.apps.hqadmin.service_checks.get_kafka_client')
    def test_check_kafka(self, kafka_client):
        kafka_client.return_value = KafkaMock(1, 1)
        x = check_kafka()
        self.assertEqual(x.msg, 'Kafka seems to be in order')

    @run_with_all_backends
    @patch('corehq.apps.hqadmin.service_checks.get_kafka_client')
    def test_check_kafka_no_brokers(self, kafka_client):
        kafka_client.return_value = KafkaMock(0, 1)
        x = check_kafka()
        self.assertEqual(x.msg, 'No Kafka brokers found')

    @run_with_all_backends
    @patch('corehq.apps.hqadmin.service_checks.get_kafka_client')
    def test_check_kafka_no_topics(self, kafka_client):
        kafka_client.return_value = KafkaMock(1, 0)
        x = check_kafka()
        self.assertEqual(x.msg, 'No Kafka topics found')

    def test_check_postgres(self):
        x = check_postgres()
        self.assertIn('default:test_commcarehq:OK', x.msg)

    def test_check_couch(self):
        x = check_couch()
        self.assertEqual(x.msg, 'Successfully queried an arbitrary couch view')

    def test_run_checks(self):
        x = run_checks(['couch'])
        name, result = x[0]
        self.assertEqual(name, 'couch')
        self.assertEqual(result.msg, 'Successfully queried an arbitrary couch view')
