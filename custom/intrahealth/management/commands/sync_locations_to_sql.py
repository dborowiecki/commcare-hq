from django.core.management import BaseCommand

from corehq.apps.locations.models import LocationType, Location, SQLLocation


class Command(BaseCommand):

    def _sync_location(self, domain, location, id_to_location):
        if not location['doc']['lineage']:
            return self._get_or_create_location(
                domain,
                location['doc']['name'],
                location['doc']['_id'],
                location['doc']['site_code'],
                location['doc']['location_type']
            )
        else:
            parent = self._sync_location(domain, id_to_location[location['doc']['lineage'][0]], id_to_location)
            return self._get_or_create_location(
                domain,
                location['doc']['name'],
                location['doc']['_id'],
                location['doc']['site_code'],
                location['doc']['location_type'],
                parent=parent
            )

    def locations_by_domain(self, domain):
        return list(Location.get_db().view(
            'commtrack/locations_by_code',
            start_key=[domain, ''],
            end_key=[domain, 'zzzzzzz', {}],
            include_docs=True
        ))

    def _get_or_create_location(self, domain, name, location_id, site_code, location_type, parent=None):
        sql_location, created = SQLLocation.objects.get_or_create(
            site_code=site_code,
            domain=domain,
            location_type=LocationType.objects.get(name=location_type, domain=domain)
        )
        if not created:
            return sql_location
        else:
            sql_location.name = name
            sql_location.location_id = location_id
            sql_location.parent = parent
            sql_location.save()
            return sql_location

    def handle(self, domain, *args, **options):
        locations = self.locations_by_domain(domain)
        id_to_location = dict([(location['doc']['_id'], location) for location in locations])
        for location in locations:
            self._sync_location(domain, location, id_to_location)
