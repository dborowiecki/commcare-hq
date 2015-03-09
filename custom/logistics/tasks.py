from datetime import datetime
from functools import partial
import itertools
from corehq.apps.commtrack.models import SupplyPointCase
from corehq.apps.locations.models import SQLLocation, Location
from custom.ewsghana.models import EWSGhanaConfig
from custom.ewsghana.utils import get_reporting_types
from custom.ilsgateway import TEST
from custom.ilsgateway.models import ILSGatewayConfig
from custom.logistics.commtrack import save_stock_data_checkpoint, synchronization
from custom.logistics.models import StockDataCheckpoint
from celery.task.base import task
from dimagi.utils.couch.database import iter_docs


@task
def stock_data_task(domain, endpoint, apis, test_facilities=None):
    # checkpoint logic
    start_date = datetime.today()
    try:
        checkpoint = StockDataCheckpoint.objects.get(domain=domain)
        api = checkpoint.api
        date = checkpoint.date
        limit = checkpoint.limit
        offset = checkpoint.offset
        location = checkpoint.location
        if not checkpoint.start_date:
            checkpoint.start_date = start_date
            checkpoint.save()
        else:
            start_date = checkpoint.start_date
    except StockDataCheckpoint.DoesNotExist:
        checkpoint = StockDataCheckpoint()
        checkpoint.domain = domain
        checkpoint.start_date = start_date
        api = 'stock_transaction'
        date = None
        limit = 1000
        offset = 0
        location = None

    supply_points_ids = SQLLocation.objects.filter(
        domain=domain,
        location_type__in=get_reporting_types(domain)
    ).order_by('created_at').values_list('supply_point_id', flat=True)
    facilities = [doc['external_id'] for doc in iter_docs(SupplyPointCase.get_db(), supply_points_ids)]
    print len(facilities)

    apis_from_checkpoint = itertools.dropwhile(lambda x: x[0] != api, apis)
    facilities_copy = list(facilities)
    if location:
        supply_point = SupplyPointCase.view(
            'commtrack/supply_point_by_loc',
            key=[location.domain, location.location_id],
            include_docs=True,
            classes={'CommCareCase': SupplyPointCase},
        ).one()
        external_id = supply_point.external_id if supply_point else None
        if external_id:
            facilities = itertools.dropwhile(lambda x: int(x) != int(external_id), facilities)

    for idx, (api_name, api_function) in enumerate(apis_from_checkpoint):
        api_function(
            domain=domain,
            checkpoint=checkpoint,
            date=date,
            limit=limit,
            offset=offset,
            endpoint=endpoint,
            facilities=facilities
        )
        limit = 1000
        offset = 0
        # todo: see if we can avoid modifying the list of facilities in place
        if idx == 0:
            facilities = facilities_copy
    save_stock_data_checkpoint(checkpoint, apis[0][0], 100, 0, start_date, None, False)
    checkpoint.start_date = None
    checkpoint.save()


@task
def sms_users_fix(api):
    endpoint = api.endpoint
    enabled_domains = ILSGatewayConfig.get_all_enabled_domains() + EWSGhanaConfig.get_all_enabled_domains()
    synchronization(None, endpoint.get_smsusers, partial(api.add_language_to_user, domains=enabled_domains),
                    None, None, 100, 0)


@task
def locations_fix(domain):
    locations = SQLLocation.objects.filter(domain=domain, location_type__in=['country', 'region', 'district'])
    for loc in locations:
        sp = Location.get(loc.location_id).linked_supply_point()
        if sp:
            sp.external_id = None
            sp.save()
        else:
            fake_location = Location(
                _id=loc.location_id,
                name=loc.name,
                domain=domain
            )
            SupplyPointCase.get_or_create_by_location(fake_location)


@task
def add_products_to_loc(api):
    endpoint = api.endpoint
    synchronization(None, endpoint.get_locations, api.location_sync, None, None, 100, 0,
                    filters={"is_active": True})
