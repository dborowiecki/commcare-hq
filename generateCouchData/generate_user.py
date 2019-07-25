from __future__ import absolute_import
from __future__ import print_function
import corehq.apps.users.models as model
from corehq.apps.domain.models import Domain


class User:
    def __init__(self, user):
        self.user = user


class UserGenerator:
    ROLES = {
        'editor': 'edit-apps',
        'implementer': 'field-implementer',
        'reader': 'read-only',
        'admin': 'admin'
    }
    USER_TYPES = ['CommcareUser', 'WebUser']

    @classmethod
    def create_user(cls, domain, username, password='password', email=None, uuid='', date='',
                    first_name='', last_name='', user_type='CommcareUser', **kwargs):
        kwargs['device_id'] = "Generated from HQ"
        kwargs['user_data'] = {}

        if user_type == 'CommcareUser':
            user = model.CommCareUser().create(domain, username, password, email=email, uuid=uuid, date=date,
                                               first_name=first_name, last_name=last_name, **kwargs)
        elif user_type == 'WebUser':
            print('Creating web user')
            user = model.WebUser().create(domain, username, password, email=email, uuid=uuid, date=date,
                                          first_name=first_name, last_name=last_name, **kwargs)
        else:
            raise ValueError('Invalid user type')

        user.save()

        cls.get_user_by_name(username)

        return user

    @classmethod
    def get_user_by_name(cls, name):
        fromdb = model.CommCareUser().get_by_username(name)
        return fromdb

    @classmethod
    def set_user_location(cls, user, location_name):

        return

    @classmethod
    def add_superuser_status(cls, user):
        user.is_superuser = True
        user.save()

    @classmethod
    def make_inactive(cls, user):
        user.is_active = False
        user.save()

    @classmethod
    def add_to_domain(cls, user, domain_name):
        user.add_domain_membership(domain_name)
        user.save()

    @classmethod
    def set_role(cls, user, role, domains=None):
        if role not in cls.ROLES:
            raise ValueError('Role name is invalid')

        if domains is None:
            domains = user.get_domains()

        for domain in domains:
            user.set_role(domain, cls.ROLES[role])

        user.save()
