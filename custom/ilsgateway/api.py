import logging
from jsonobject import JsonObject
from jsonobject.properties import StringProperty, BooleanProperty, DecimalProperty, ListProperty, IntegerProperty,\
    FloatProperty, DictProperty
from requests.exceptions import ConnectionError
from corehq import Domain
from corehq.apps.commtrack.models import SupplyPointCase, CommtrackConfig, CommtrackActionConfig
from corehq.apps.locations.models import SQLLocation
from corehq.apps.locations.schema import LocationType
from corehq.apps.programs.models import Program
from corehq.apps.users.models import UserRole
from custom.api.utils import apply_updates
from custom.ilsgateway.models import SupplyPointStatus, DeliveryGroupReport, HistoricalLocationGroup
from custom.ilsgateway.utils import get_supply_point_by_external_id
from custom.logistics.api import LogisticsEndpoint, APISynchronization, LogisticsProductSync, ObjectSync, \
    LogisticsWebUserSync, LogisticsSMSUserSync
from corehq.apps.locations.models import Location as Loc

LOCATION_TYPES = ["MOHSW", "REGION", "DISTRICT", "FACILITY"]


class Product(JsonObject):
    name = StringProperty()
    units = StringProperty()
    sms_code = StringProperty()
    description = StringProperty()
    is_active = BooleanProperty()


class ILSUser(JsonObject):
    username = StringProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    email = StringProperty()
    password = StringProperty()
    is_staff = BooleanProperty(default=False)
    is_active = BooleanProperty()
    is_superuser = BooleanProperty(default=False)
    last_login = StringProperty()
    date_joined = StringProperty()
    location = DecimalProperty()
    supply_point = IntegerProperty()


class SMSUser(JsonObject):
    id = IntegerProperty()
    name = StringProperty()
    role = StringProperty()
    is_active = StringProperty()
    supply_point = DecimalProperty()
    email = StringProperty()
    phone_numbers = ListProperty()
    backend = StringProperty()
    date_updated = StringProperty()
    language = StringProperty()


class Location(JsonObject):
    id = IntegerProperty()
    name = StringProperty()
    type = StringProperty()
    parent_id = IntegerProperty()
    latitude = StringProperty()
    longitude = StringProperty()
    code = StringProperty()
    groups = ListProperty()
    historical_groups = DictProperty()


class ProductStock(JsonObject):
    supply_point = IntegerProperty()
    quantity = FloatProperty()
    product = StringProperty()
    last_modified = StringProperty()
    auto_monthly_consumption = FloatProperty()


class StockTransaction(JsonObject):
    beginning_balance = DecimalProperty()
    date = StringProperty()
    ending_balance = DecimalProperty()
    product = StringProperty()
    quantity = DecimalProperty()
    report_type = StringProperty()
    supply_point = IntegerProperty()


def _get_location_id(facility, domain):
    return get_supply_point_by_external_id(domain, facility).location_id


class ILSGatewayEndpoint(LogisticsEndpoint):

    models_map = {
        'product': Product,
        'webuser': ILSUser,
        'smsuser': SMSUser,
        'location': Location,
        'product_stock': ProductStock,
        'stock_transaction': StockTransaction
    }

    def __init__(self, base_uri, username, password):
        super(ILSGatewayEndpoint, self).__init__(base_uri, username, password)
        self.supplypointstatuses_url = self._urlcombine(self.base_uri, '/supplypointstatus/')
        self.deliverygroupreports_url = self._urlcombine(self.base_uri, '/deliverygroupreports/')

    def get_supplypointstatuses(self, domain, facility, **kwargs):
        meta, supplypointstatuses = self.get_objects(self.supplypointstatuses_url, **kwargs)
        location_id = _get_location_id(facility, domain)
        return meta, [SupplyPointStatus.wrap_from_json(supplypointstatus, location_id) for supplypointstatus in
                      supplypointstatuses]

    def get_deliverygroupreports(self, domain, facility, **kwargs):
        meta, deliverygroupreports = self.get_objects(self.deliverygroupreports_url, **kwargs)
        location_id = _get_location_id(facility, domain)
        return meta, [DeliveryGroupReport.wrap_from_json(deliverygroupreport, location_id)
                      for deliverygroupreport in deliverygroupreports]


class ILSProductSync(LogisticsProductSync):

    @property
    def name(self):
        return "product"

    def sync_object(self, ilsgateway_product, **kwargs):
        from custom.ilsgateway import PRODUCTS_CODES_PROGRAMS_MAPPING
        product = super(ILSProductSync, self).sync_object(ilsgateway_product)
        programs = list(Program.by_domain(self.domain))
        for program, products in PRODUCTS_CODES_PROGRAMS_MAPPING.iteritems():
            if product.code in products:
                existing_program = filter(lambda p: p.name == program, programs)
                if not existing_program:
                    new_program = Program(domain=self.domain)
                    new_program.name = program
                    new_program.save()
                    product.program_id = new_program.get_id
                    product.save()
                else:
                    product.program_id = existing_program[0].get_id
                    product.save()
        return product


class ILSLocationSync(ObjectSync):

    def __init__(self, endpoint, domain, location_type, checkpoint=None, filters=None):
        super(ILSLocationSync, self).__init__(endpoint, domain, checkpoint, filters)
        self.location_type = location_type

    @property
    def name(self):
        return "location_%s" % self.location_type

    def get_object(self, object_id):
        return self.endpoint.get_location(object_id)

    def get_objects(self, *args, **kwargs):
        return self.endpoint.get_locations(**kwargs)

    def sync_object(self, ilsgateway_location, **kwargs):
        try:
            sql_loc = SQLLocation.objects.get(
                domain=self.domain,
                external_id=int(ilsgateway_location.id)
            )
            location = Loc.get(sql_loc.location_id)
        except SQLLocation.DoesNotExist:
            location = None
        except SQLLocation.MultipleObjectsReturned:
            return

        if not location:
            if ilsgateway_location.parent_id:
                try:
                    sql_loc_parent = SQLLocation.objects.get(
                        domain=self.domain,
                        external_id=ilsgateway_location.parent_id
                    )
                    loc_parent = sql_loc_parent.couch_location()
                except SQLLocation.DoesNotExist:
                    parent = self.endpoint.get_location(ilsgateway_location.parent_id)
                    loc_parent = self.sync_object(Location(parent))
                location = Loc(parent=loc_parent)
            else:
                location = Loc()
                location.lineage = []
            location.domain = self.domain
            location.name = ilsgateway_location.name
            if ilsgateway_location.groups:
                location.metadata = {'groups': ilsgateway_location.groups}
            if ilsgateway_location.latitude:
                location.latitude = float(ilsgateway_location.latitude)
            if ilsgateway_location.longitude:
                location.longitude = float(ilsgateway_location.longitude)
            location.location_type = ilsgateway_location.type
            location.site_code = ilsgateway_location.code
            location.external_id = unicode(ilsgateway_location.id)
            location.save()

            if ilsgateway_location.type == 'FACILITY' and not SupplyPointCase.get_by_location(location):
                SupplyPointCase.create_from_location(self.domain, location)
                location.save()
        else:
            location_dict = {
                'name': ilsgateway_location.name,
                'latitude': float(ilsgateway_location.latitude) if ilsgateway_location.latitude else None,
                'longitude': float(ilsgateway_location.longitude) if ilsgateway_location.longitude else None,
                'location_type': ilsgateway_location.type,
                'site_code': ilsgateway_location.code.lower(),
                'external_id': str(ilsgateway_location.id),
                'metadata': {}
            }
            if ilsgateway_location.groups:
                location_dict['metadata']['groups'] = ilsgateway_location.groups
            case = SupplyPointCase.get_by_location(location)
            if apply_updates(location, location_dict):
                location.save()
                if case:
                    case.update_from_location(location)
                else:
                    SupplyPointCase.create_from_location(self.domain, location)

        if ilsgateway_location.historical_groups:
            historical_groups = ilsgateway_location.historical_groups
        else:
            counter = 0
            historical_groups = {}
            while counter != 5:
                try:
                    # todo: we may be able to avoid this call by passing the groups in as part of the original
                    # location dict, though that may introduce slowness/timeouts
                    location_object = self.endpoint.get_location(
                        ilsgateway_location.id,
                        params=dict(with_historical_groups=1)
                    )
                    historical_groups = Location(**location_object).historical_groups
                    break
                except ConnectionError as e:
                    logging.error(e)
                    counter += 1

        for date, groups in historical_groups.iteritems():
            for group in groups:
                HistoricalLocationGroup.objects.get_or_create(date=date, group=group,
                                                              location_id=location.sql_location)
        return location


class ILSWebUserSync(LogisticsWebUserSync):

    @property
    def name(self):
        return "webuser"

    def sync_object(self, ilsgateway_webuser, **kwargs):
        web_user = super(ILSWebUserSync, self).sync_object(ilsgateway_webuser)
        if not web_user:
            return None
        dm = web_user.get_domain_membership(self.domain)
        dm.role_id = UserRole.get_read_only_role_by_domain(self.domain).get_id
        web_user.save()
        return web_user


class ILSSMSUserSync(LogisticsSMSUserSync):

    @property
    def name(self):
        return "smsuser"

    def sync_object(self, ilsgateway_smsuser, **kwargs):
        sms_user = super(ILSSMSUserSync, self).sync_object(ilsgateway_smsuser, **kwargs)
        if not sms_user:
            return None
        try:
            location = SQLLocation.objects.get(domain=self.domain, external_id=ilsgateway_smsuser.supply_point)
            sms_user.set_location(location.location_id)
        except SQLLocation.DoesNotExist:
            pass
        sms_user.save()
        return sms_user


class ILSGatewayAPI(APISynchronization):

    LOCATION_CUSTOM_FIELDS = [
        {'name': 'groups'},
    ]
    SMS_USER_CUSTOM_FIELDS = [
        {
            'name': 'role',
            'choices': [
                "district supervisor",
                "MSD",
                "imci coordinator",
                "Facility in-charge",
                "MOHSW",
                "RMO",
                "District Pharmacist",
                "DMO",
            ]
        },
        {'name': 'backend'},
    ]
    PRODUCT_CUSTOM_FIELDS = []

    @property
    def apis(self):
        return [
            ILSProductSync(self.endpoint, self.domain, self.checkpoint),
            ILSLocationSync(self.endpoint, self.domain, 'region', self.checkpoint,
                            filters=dict(type='region')),
            ILSLocationSync(self.endpoint, self.domain, 'district', self.checkpoint,
                            filters=dict(type='district')),
            ILSLocationSync(self.endpoint, self.domain, 'facility', self.checkpoint,
                            filters=dict(type='facility')),
            ILSWebUserSync(self.endpoint, self.checkpoint, self.domain),
            ILSSMSUserSync(self.endpoint, self.checkpoint, self.domain)
        ]

    def prepare_commtrack_config(self):
        """
        Bootstraps the domain-level metadata according to the static config.
        - Sets the proper location types hierarchy on the domain object.
        - Sets a keyword handler for reporting receipts
        """
        domain = Domain.get_by_name(self.domain)
        domain.location_types = []
        for i, value in enumerate(LOCATION_TYPES):
            allowed_parents = [LOCATION_TYPES[i - 1]] if i > 0 else [""]
            domain.location_types.append(
                LocationType(name=value, allowed_parents=allowed_parents,
                             administrative=(value.lower() != 'facility')))
        domain.save()
        config = CommtrackConfig.for_domain(self.domain)
        actions = [action.keyword for action in config.actions]
        if 'delivered' not in actions:
            config.actions.append(
                CommtrackActionConfig(
                    action='receipts',
                    keyword='delivered',
                    caption='Delivered')
            )
            config.save()

