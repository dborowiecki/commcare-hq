from django.core.management import BaseCommand

from corehq.apps.domain.models import Domain
from corehq.apps.locations.models import LocationType


class Command(BaseCommand):

    def _sync_location_type(self, domain, location_type, id_to_type):
        if not location_type.parent_type_id:
            location_type = LocationType.objects.get_or_create(
                domain=domain,
                name=location_type.name,
                administrative=location_type.administrative
            )[0]
        else:
            parent = self._sync_location_type(domain, id_to_type[location_type.parent_type_id], id_to_type)
            location_type = LocationType.objects.get_or_create(
                domain=domain,
                name=location_type.name,
                administrative=location_type.administrative,
                parent_type=parent
            )[0]
        return location_type

    def handle(self, domain, *args, **options):
        domain = Domain.get_by_name(domain)
        location_types = domain.location_types
        id_to_type = dict([(location_type.id, location_type) for location_type in location_types])
        for location_type in location_types:
            self._sync_location_type(domain, location_type, id_to_type)
