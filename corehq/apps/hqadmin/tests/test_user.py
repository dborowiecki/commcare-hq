import base64
import json

from django.contrib import auth
from django.test import Client, TestCase
from django.urls import reverse

from corehq.apps.domain.models import Domain
from corehq.apps.hqadmin.views import SuperuserManagement
from corehq.apps.users.models import CommCareUser, WebUser


class TestUserViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestUserViews, cls).setUpClass()
        cls.make_domain()
        cls.make_worker()
        cls.create_client()

    @classmethod
    def tearDownClass(cls):
        cls.super_worker.delete()
        cls.domain.delete()
        super(TestUserViews, cls).tearDownClass()

    @classmethod
    def make_worker(cls):
        cls.super_worker = WebUser.create(
            domain=None,
            username='ninasimone@dimagi.com',
            password='123',
            is_superuser=True,
        )
        cls.super_worker.add_domain_membership(cls.domain_name, is_admin=True)
        cls.super_worker.set_role(cls.domain.name, 'admin')
        cls.super_worker.save()

    def _create_non_superuser(self, username=None):
        soon_superuser = WebUser.create(
            domain=None,
            username=username or 'ellafitzgerald@dimagi.com',
            password='123'
        )
        soon_superuser.save()
        self.addCleanup(soon_superuser.delete)

    @classmethod
    def make_domain(cls):
        cls.domain_name = 'd00main'
        cls.domain = Domain.get_or_create_with_name(cls.domain_name, is_active=True)
        cls.domain.save()

    @property
    def url(self):
        return reverse(SuperuserManagement.urlname)

    @classmethod
    def create_client(cls):
        cls.client = Client()

    def test_valid_data(self):
        self._create_non_superuser()
        data = {
            'csv_email_list': 'ellafitzgerald@dimagi.com',
            'privileges': 'is_superuser'
        }
        self.client.login(
            username=self.super_worker.username,
            password='123'
        )

        response = self.client.post(self.url, data, follow=True)
        user_now = WebUser.get_by_username('ellafitzgerald@dimagi.com')
        self.assertTrue(user_now.is_superuser, True)
        self.assertEqual(response.status_code, 200)
