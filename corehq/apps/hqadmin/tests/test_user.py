# import json
#
# from django.test import Client, TestCase
# from django.urls import reverse
#
# from corehq.apps.domain.models import Domain
# from corehq.apps.hqadmin.views import SuperuserManagement
# from corehq.apps.users.models import CommCareUser, WebUser
#
#
# class TestUserViews(TestCase):
#
#     @classmethod
#     def setUpClass(cls):
#         super(TestUserViews, cls).setUpClass()
#         cls.make_domain()
#         cls.make_worker()
#         cls.create_client()
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.mobile_worker.delete()
#         cls.domain.delete()
#         super(TestUserViews, cls).tearDownClass()
#
#     @classmethod
#     def make_worker(cls):
#         cls.mobile_worker = WebUser.create(
#             None,
#             'nina_simone@dimagi.com',
#             '123',
#             is_superuser=True,
#         )
#         cls.mobile_worker.add_domain_membership(cls.domain_name, is_admin=True)
#         cls.mobile_worker.save()
#
#     @classmethod
#     def make_domain(cls):
#         cls.domain_name = 'd00main'
#         cls.domain = Domain.get_or_create_with_name(cls.domain_name, is_active=True)
#         cls.domain.save()
#
#     @property
#     def url(self):
#         return reverse(SuperuserManagement.urlname)
#
#     @classmethod
#     def create_client(cls):
#         cls.client = Client()
#         login = cls.client.login(
#             username='nina_simone@dimagi.com',
#             password='123'
#         )
#
#
#     def test_valid_data(self):
#         management = SuperuserManagement()
#         soon_superuser = WebUser.create(
#             self.domain_name,
#             'ella_fitzgerald@dimagi.com',
#             '123'
#         )
#         self.addCleanup(soon_superuser.delete)
#
#         data = {
#             'username': self.mobile_worker.username,
#             'password': '123',
#             'csv_email_list': 'ella_fitzgerald@dimagi.com',
#             'privileges': 'is_superuser'
#         }
#
#         response = self.client.post(self.url, data, follow=True)
#         #self.assertTrue(soon_superuser.is_superuser, True)
