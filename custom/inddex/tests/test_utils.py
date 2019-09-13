from django.test import TestCase

from corehq.apps.domain.models import Domain
from corehq.apps.locations.models import LocationType, SQLLocation
from corehq.apps.users.models import CommCareUser, WebUser
from corehq.util.test_utils import PatchMeta


class InddexTestCase(TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.domain_name = 'inddex-best-test'
        cls.domain = Domain.get_or_create_with_name(cls.domain_name)

        cls.parent_location_type = LocationType.objects.get_or_create(
            domain=cls.domain.name,
            name='parent type',
            code='parent'
        )[0]

        cls.child_location_type = LocationType.objects.get_or_create(
            domain=cls.domain.name,
            name='child type',
            code='child',
            parent_type=cls.parent_location_type
        )[0]

        cls.parent_location = SQLLocation.objects.get_or_create(
            domain=cls.domain.name,
            name='parent_location',
            site_code='parent',
            location_type=cls.parent_location_type
        )[0]

        cls.child_location = SQLLocation.objects.get_or_create(
            domain=cls.domain.name,
            name='child_location',
            site_code='child',
            location_type=cls.child_location_type,
            parent=cls.parent_location
        )[0]

        cls.user = WebUser.create(cls.domain.name, 'louis', 'prima')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.child_location.delete()
        cls.parent_location.delete()
        cls.child_location_type.delete()
        cls.parent_location_type.delete()
        cls.domain.delete()

