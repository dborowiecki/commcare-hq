from sqlagg.columns import SimpleColumn

from corehq.apps.locations.models import SQLLocation, LocationType
from corehq.apps.reports.sqlreport import SqlData, DatabaseColumn
from corehq.apps.userreports.util import get_table_name

from django.core.management import CommandError
from django.core.management.base import BaseCommand


class ChampFilter(SqlData):

    domain = 'ipm-senegal'
    table = 'operateur_combined'
    column_names = [
        'region_id',
        'region_name',
        'district_id',
        'district_name',
        'pps_id',
        'pps_name',
    ]

    def __init__(self):
        config = {
            'domain': self.domain,
        }
        super(ChampFilter, self).__init__(config)

    @property
    def table_name(self):
        return get_table_name(self.domain, self.table)

    @property
    def group_by(self):
        return self.column_names

    @property
    def filters(self):
        return []

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def columns(self):
        return [
            DatabaseColumn(column, SimpleColumn(column)) for column in self.column_names
        ]

    @property
    def data(self):
        return self.get_data()


class Command(BaseCommand):

    help = 'Adds locations needed for IPM based on ucr_ipm-senegal_operateur_combined_fe20409e table'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        rows = ChampFilter().data
        locations_data = []
        site_code = 0

        # ['region_id', 'district_id', 'pps_id', 'district_name', 'pps_name', 'region_name']
        # SQLLocation(name)
        for row in rows:
            pps_id = row['pps_id']
            pps_name = row['pps_name']
            pps_exists = SQLLocation.objects.filter(location_id__exact=pps_id).exists()
            if not pps_exists:
                district_id = row['district_id']
                district_name = row['district_name']
                district_exists = SQLLocation.objects.filter(location_id__exact=district_id).exists()
                if not district_exists:
                    region_id = row['region_id']
                    region_name = row['region_name']
                    region_exists = SQLLocation.objects.filter(location_id__exact=region_id).exists()
                    if not region_exists:
                        location_type = LocationType.objects.get(name='region', domain='ipm-senegal')
                        location_type_id = location_type.id
                        SQLLocation.objects.create(domain='ipm-senegal', name=region_name,
                                                   location_id=region_id,
                                                   location_type_id=location_type_id,
                                                   site_code=site_code)
                        site_code += 1
                    location_type = LocationType.objects.get(name='district', domain='ipm-senegal')
                    location_type_id = location_type.id
                    parent = SQLLocation.objects.get(location_id__exact=region_id)
                    parent_id = parent.id
                    SQLLocation.objects.create(domain='ipm-senegal', name=district_name,
                                               location_id=district_id,
                                               location_type_id=location_type_id,
                                               site_code=site_code,
                                               parent_id=parent_id)
                    site_code += 1
                location_type = LocationType.objects.get(name='pps', domain='ipm-senegal')
                location_type_id = location_type.id
                parent = SQLLocation.objects.get(location_id__exact=district_id)
                parent_id = parent.id
                SQLLocation.objects.create(domain='ipm-senegal', name=pps_name,
                                           location_id=pps_id,
                                           location_type_id=location_type_id,
                                           site_code=site_code,
                                           parent_id=parent_id)
                site_code += 1
        print('Created {} locations'.format(site_code))
