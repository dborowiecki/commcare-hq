from __future__ import absolute_import
from __future__ import unicode_literals

from django.test.client import Client
from django.urls import reverse
import os
import requests
from requests.auth import HTTPDigestAuth, HTTPProxyAuth

from corehq.apps.receiverwrapper import views as form_submition
from corehq.apps.app_manager.models import AdvancedModule, Application, Module
from corehq.apps.receiverwrapper.auth import AuthContext
from corehq.form_processor.interfaces.dbaccessors import FormAccessors
from corehq.form_processor.submission_post import SubmissionPost
from corehq.form_processor.tests.utils import use_sql_backend, FormProcessorTestUtils
from corehq.apps.users.models import CommCareUser
from corehq.apps.app_manager.util import save_xform
from .generate_domain import  DomainGenerator
from .generate_user import UserGenerator

class AppGenerator:
    @classmethod
    def generate_app(cls, domain_name, app_name='Undefined App'):
        app = Application.new_app(domain_name, app_name)
        app.save()
        return app

    @classmethod
    def get_domain_apps(cls, domain):
        return domain.full_applications()

    @classmethod
    def generate_module(cls, app, module_name='Unfefined Module'):
        module = Module.new_module(module_name, None)
        app.add_module(module)
        app.save()
        return module

    @classmethod
    def generate_form(cls, app, module, form_name='Undefined Form'):
        form = app.new_form(module.id, form_name, None)
        app.save()
        return form


class FormGenerator:

    def __init__(self, domain, user=None):
        self.domain = DomainGenerator.create_domain("submit2")
        self.domain.is_active = True
        self.domain.save()
        self.couch_user = CommCareUser.create(self.domain.name, "test", "foobar")

    #    self.client = Client()
    #    log = self.client.login(**{'username': 'test', 'password': 'foobar'})
    #    self.url = reverse("receiver_post", args=[self.domain])
        self.url = 'http://localhost:8000/a/submit2/receiver/'
        out = self._submit('simple_form.xml')
      #  form_id = out['X-CommCareHQ-FormID']
        print('Text:\n\n{}\n\n'.format(len(out.text)))
        print('Response content: {}'.format(out.content))
        print('Response status code: {}'.format(out.status_code))
        print(out.headers.items())
      #   FormProcessorTestUtils.delete_all_xforms(self.domain.name)
      #   FormProcessorTestUtils.delete_all_cases(self.domain.name)
      #  self.couch_user.delete()
      #  self.domain.delete()

    def _submit(self, formname, **extra):
        file_path = os.path.join(os.path.dirname(__file__), "data", formname)
        attachments = extra.pop("attachments", None)
        url = extra.pop('url', self.url)
        print("URL: {}".format(url))
        with open(file_path, "rb") as f:
            data = {"xml_submission_file": f}
            if attachments:
                data.update(attachments)

            with requests.Session() as s:
                log_url = 'http://localhost:8000/accounts/login/'
                log_data = {'auth-username': self.couch_user.username,
                            'auth-password': self.couch_user.password}
                p = s.post(log_url, log_data)
                print('Login code: {}'.format(p.status_code))
                f = s.post(self.url, data)
                print('Request status code: {}'.format(f.status_code))
                return f

        #    return requests.post(self.url, data=data)
        #    return self.client.post(url, data, **extra)

    def add_form(self, formname, HTTP_DATE='Tue, 23 Jul 2019 15:47:32 GMT'):
        '''

        :param formname: Name of file with form in data folder
        :param HTTP_DATE: date in http format when form was sent
        :return: true if successful addition of form
        '''
        response = self._submit(formname, HTTP_DATE=HTTP_DATE)
        print("RESPONSE: ")
        print(response)
        xform_id = response['X-CommCareHQ-FormID']
        foo = FormAccessors(self.domain.name).get_form(xform_id).to_json()
        return foo['received_on']

    @classmethod
    def delete_domain_forms(cls, domain):
        FormProcessorTestUtils.delete_all_xforms(domain.name)
        FormProcessorTestUtils.delete_all_cases(domain.name)


class FormGenerator2:
    @classmethod
    def foo(cls):
        file_path = os.path.join(os.path.dirname(__file__), "data", 'simple_form.xml')
        domain = DomainGenerator.create_domain('4thdomain')
        app = AppGenerator.get_domain_apps(domain)[0]
        user = UserGenerator.get_user_by_name("test2")
        if user is None:
            user = CommCareUser.create(domain.name, "test2", "foobar")

        print(user.user_id)
        import datetime
        dt = datetime.datetime(2019, 7, 23)
        with open(file_path, "r") as f:
            #print(type(f.read()))
            submission_post = SubmissionPost(
                instance=f.read(),
                attachments=None,
                domain=domain.name,
                app_id='4pp9id',
                build_id='4ppbui1d',
                auth_context=AuthContext(
                    domain=domain.name,
                    user_id=user.user_id,
                    authenticated=True,
                ),
                location='1oc4ti0n',
                received_on=dt,
                date_header='Tue, 23 Jul 2019 15:47:32 GMT',
                path='p4th',
                submit_ip='12345',
                last_sync_token=None,
                openrosa_headers=None,
            )
            x = submission_post.run()
            d = x.response
            form_id = d['X-CommCareHQ-FormID']
            print('Form id: {}'.format(form_id))
            foo = FormAccessors(domain.name).get_form(form_id)
            print(type(FormAccessors(domain.name).get_form(form_id)))
            bar = FormAccessors(domain.name).get_all_form_ids_in_domain()
            a = bar[0]
            foo['doc_type'] = 'xforminstance'
            FormAccessors(domain.name).save_new_form(foo)
            foo = FormAccessors(domain.name).get_form(form_id)

            print('All forms: \n{}'.format(len(bar)))
            print('Received form: \n{}'.format(foo.to_json()))
            print('Doc type: \n{}'.format(foo['doc_type']))
