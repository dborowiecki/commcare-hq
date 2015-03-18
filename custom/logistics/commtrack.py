import itertools
from functools import partial
import logging
import traceback
from corehq.apps.commtrack.models import SupplyPointCase

from corehq.apps.locations.models import Location
from custom.logistics.models import MigrationCheckpoint
from requests.exceptions import ConnectionError
from datetime import datetime
from custom.ilsgateway.utils import get_next_meta_url


def retry(retry_max):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            retry_count = 0
            fail = False
            result = None
            while retry_count < retry_max:
                try:
                    result = f(*args, **kwargs)
                    fail = False
                    break
                except Exception:
                    retry_count += 1
                    fail = True
                    logging.error('%d/%d tries failed' % (retry_count, retry_max))
                    logging.error(traceback.format_exc())
            if fail:
                logging.error(f.__name__ + ": number of tries exceeds limit")
                logging.error("args: %s, kwargs: %s" % (args, kwargs))
            return result
        return wrapped_f
    return wrap


def synchronization(sync_api, **kwargs):
    has_next = True
    next_url = ""
    while has_next:
        meta, objects = sync_api.get_objects_with_filters(
            next_url_params=next_url,
            **kwargs
        )
        for obj in objects:
            sync_api.sync_object(obj)
        sync_api.update_checkpoint()
        has_next, next_url = get_next_meta_url(has_next, meta, next_url)


def save_checkpoint(checkpoint, api, limit, offset, date, commit=True):
    checkpoint.limit = limit
    checkpoint.offset = offset
    checkpoint.api = api
    checkpoint.date = date
    if commit:
        checkpoint.save()


def save_stock_data_checkpoint(checkpoint, api, limit, offset, date, external_id, commit=True):
    save_checkpoint(checkpoint, api, limit, offset, date, False)
    if external_id:
        supply_point = SupplyPointCase.view('hqcase/by_domain_external_id',
                                            key=[checkpoint.domain, str(external_id)],
                                            reduce=False,
                                            include_docs=True).first()
        if not supply_point:
            return
        checkpoint.location = supply_point.location.sql_location
    else:
        checkpoint.location = None
    if commit:
        checkpoint.save()


def add_location(user, location_id):
    if location_id:
        loc = Location.get(location_id)
        user.clear_locations()
        user.add_location(loc, create_sp_if_missing=True)


def check_hashes(webuser, django_user, password):
    if webuser.password == password and django_user.password == password:
        return True
    else:
        logging.warning("Logistics: Hashes are not matching for user: %s" % webuser.username)
        return False


def bootstrap_domain(api_object, **kwargs):
    api_object.set_default_backend()
    api_object.prepare_custom_fields()
    api_from_checkpoint = api_object.checkpoint.api
    apis = api_object.apis
    if api_from_checkpoint:
        apis = itertools.dropwhile(lambda x: x.name != api_object.checkpoint.api, api_object.apis)

    for idx, api in enumerate(apis):
        if idx != 0:
            api.init_checkpoint()
        synchronization(api, **kwargs)
    api_object.reset_checkpoint()
