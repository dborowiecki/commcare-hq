from functools import partial
import logging
from custom.ilsgateway.commtrack import sync_ilsgateway_webuser, sync_ilsgateway_product, commtrack_settings_sync, sync_ilsgateway_smsuser, save_checkpoint, products_sync, sync_ilsgateway_location
from custom.ilsgateway.ghana.api import GhanaEndpoint
from custom.ilsgateway.ghana.commtrack import commtrack_settings_sync, save_checkpoint, sync_ilsgateway_webuser, sync_ilsgateway_product
from custom.ilsgateway.tanzania.api import TanzaniaEndpoint
from dimagi.utils.dates import force_to_datetime
from custom.ilsgateway.models import ILSMigrationCheckpoint
from requests.exceptions import ConnectionError
from datetime import datetime
from custom.ilsgateway.api import Location as Loc

def ews_smsuser_extension(sms_user, user_dict):
    sms_user.user_data['to'] = user_dict.to
    if user_dict.family_name != '':
        sms_user.__setattr__('last_name', user_dict.family_name)

    sms_user.save()
    return sms_user

def smsusers_sync(project, endpoint, checkpoint, **kwargs):
    has_next = True
    next_url = ""

    while has_next:
        meta, users = endpoint.get_smsusers(next_url_params=next_url, **kwargs)
        save_checkpoint(checkpoint, "smsuser",
                        meta.get('limit') or kwargs.get('limit'), meta.get('offset') or kwargs.get('offset'),
                        kwargs.get('date', None))
        for user_dict in users:
            sms_user = sync_ilsgateway_smsuser(project, user_dict)
            ews_smsuser_extension(sms_user, user_dict)

        if not meta.get('next', False):
            has_next = False
        else:
            next_url = meta['next'].split('?')[1] if meta['next'] else None

def ews_webuser_extension(couch_user, user_dict):
    couch_user.__setattr__('user_data', {})
    couch_user.user_data['sms_notifications'] = user_dict.sms_notifications
    couch_user.user_data['organization'] = user_dict.organization
    couch_user.save()
    return couch_user

def webusers_sync(project, endpoint, checkpoint, limit, offset, **kwargs):
    save_checkpoint(checkpoint, "webuser", limit, offset, kwargs.get('date', None))
    for user in endpoint.get_webusers(**kwargs):
        if user.email or user.username:
            couch_user = sync_ilsgateway_webuser(project, user)
            ews_webuser_extension(couch_user, user)


def ews_location_extension(location, location_dict):
    location.metadata['created_at'] = location_dict.created_at
    location.metadata['supervised_by'] = location_dict.supervised_by
    location.save()
    return location

def locations_sync(project, endpoint, checkpoint, **kwargs):
    has_next = True
    next_url = None

    while has_next:
        meta, locations = endpoint.get_locations(next_url_params=next_url, **kwargs)
        save_checkpoint(checkpoint, 'location_%s' % kwargs['filters']['type'],
                        meta.get('limit') or kwargs.get('limit'), meta.get('offset') or kwargs.get('offset'),
                        kwargs.get('date', None))
        for location_dict in locations:
            location = sync_ilsgateway_location(project, endpoint, location_dict)
            ews_location_extension(location, location_dict)

        if not meta.get('next', False):
            has_next = False
        else:
            next_url = meta['next'].split('?')[1] if meta['next'] else None


def bootstrap_domain(ilsgateway_config):
    domain = ilsgateway_config.domain
    start_date = datetime.today()
    endpoint = GhanaEndpoint.from_config(ilsgateway_config)
    try:
        checkpoint = ILSMigrationCheckpoint.objects.get(domain=domain)
        api = checkpoint.api
        date = checkpoint.date
        limit = checkpoint.limit
        offset = checkpoint.offset
        if not checkpoint.start_date:
            checkpoint.start_date = start_date
            checkpoint.save()
        else:
            start_date = checkpoint.start_date
    except ILSMigrationCheckpoint.DoesNotExist:
        checkpoint = ILSMigrationCheckpoint()
        checkpoint.domain = domain
        checkpoint.start_date = start_date
        api = 'product'
        date = None
        limit = 1000
        offset = 0
        commtrack_settings_sync(domain)

    apis = [
        ('product', partial(products_sync, domain, endpoint, checkpoint, date=date)),
        ('location_facility', partial(locations_sync, domain, endpoint, checkpoint, date=date,
                                      filters=dict(date_updated__gte=date, type='facility'))),
        ('location_district', partial(locations_sync, domain, endpoint, checkpoint, date=date,
                                      filters=dict(date_updated__gte=date, type='district'))),
        ('location_region', partial(locations_sync, domain, endpoint, checkpoint, date=date,
                                    filters=dict(date_updated__gte=date, type='region'))),
        ('webuser', partial(webusers_sync, domain, endpoint, checkpoint, date=date,
                            filters=dict(user__date_joined__gte=date))),
        ('smsuser', partial(smsusers_sync, domain, endpoint, checkpoint, date=date,
                            filters=dict(date_updated__gte=date)))
    ]

    try:
        i = 0
        while apis[i][0] != api:
            i += 1

        for api in apis[i:]:
            api[1](limit=limit, offset=offset)
            limit = 1000
            offset = 0

        save_checkpoint(checkpoint, 'product', 1000, 0, start_date, False)
        checkpoint.start_date = None
        checkpoint.save()
    except ConnectionError as e:
        logging.error(e)
