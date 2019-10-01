from datetime import datetime, date
from unittest import TestCase

from casexml.apps.case.const import CASE_ACTION_CREATE
from casexml.apps.case.models import CommCareCase, CommCareCaseAction
from casexml.apps.stock.models import StockReport, StockTransaction, const, Decimal
from corehq.apps.accounting.exceptions import NewSubscriptionError
from corehq.apps.accounting.models import Subscription, BillingAccount, SoftwarePlanEdition, DefaultProductPlan, \
    Subscriber, SubscriptionAdjustment
from corehq.apps.app_manager.models import Application, Module, Form
from corehq.apps.commtrack.const import SUPPLY_POINT_CASE_TYPE
from corehq.apps.domain.models import Domain, Deployment
from corehq.apps.groups.models import Group
from corehq.apps.locations.models import SQLLocation, LocationType
from corehq.apps.products.models import SQLProduct
from corehq.apps.sms.models import SMS
from corehq.apps.users.models import CommCareUser
from corehq.elastic import get_es_new, send_to_elasticsearch
from corehq.pillows.mappings.case_mapping import CASE_INDEX_INFO
from corehq.pillows.mappings.domain_mapping import DOMAIN_INDEX_INFO
from corehq.pillows.mappings.group_mapping import GROUP_INDEX_INFO
from corehq.pillows.mappings.sms_mapping import SMS_INDEX_INFO
from corehq.pillows.mappings.user_mapping import USER_INDEX_INFO
from corehq.pillows.mappings.xform_mapping import XFORM_INDEX_INFO
from corehq.pillows.xform import transform_xform_for_elasticsearch
from corehq.util.elastic import ensure_index_deleted
from couchforms.models import XFormInstance
from pillowtop.es_utils import initialize_index_and_mapping


class TestElasticsearchReportMixin:

    @classmethod
    def setup_class(cls):
        cls.es = get_es_new()
        cls.make_domain()
        cls.make_user()
        cls.make_case()
        cls.make_app()
        cls.make_sms()
        cls.make_xform()
        cls.add_stockreport()
        cls.make_group()
        cls.make_sqllocation()
        cls.make_domain_subscription()
        cls.send_data_to_elasticsearch()

    @classmethod
    def teardown_class(cls):
        Subscription._get_active_subscription_by_domain.clear(Subscription, cls.domain.name)
        SubscriptionAdjustment.objects.all().delete()
        cls.subscription.delete()
        cls.account.delete()
        cls.form.delete()
        cls.sms_user_recipent.delete()
        cls.sms_case_recipent.delete()
        cls.app.delete()
        cls.user.delete()
        cls.case.delete()
        cls.stock_transaction.delete()
        cls.stock_report.delete()
        cls.sql_product.delete()
        cls.group.delete()
        cls.domain.delete()
        cls.location1.delete()
        cls.location_type.delete()
        ensure_index_deleted(CASE_INDEX_INFO.index)
        ensure_index_deleted(SMS_INDEX_INFO.index)
        ensure_index_deleted(USER_INDEX_INFO.index)
        ensure_index_deleted(DOMAIN_INDEX_INFO.index)
        ensure_index_deleted(XFORM_INDEX_INFO.index)
        ensure_index_deleted(GROUP_INDEX_INFO.index)

    @classmethod
    def make_domain(cls):
        cls.domain_name = 'ta3te5t-dd0mm4aain'
        cls.domain = Domain.get_or_create_with_name(cls.domain_name, is_active=True)
        cls.add_deployment_to_domain()
        cls.domain.date_created = datetime(year=2019, month=9, day=11)
        cls.domain.save()
        ensure_index_deleted(DOMAIN_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, DOMAIN_INDEX_INFO)

        send_to_elasticsearch('domains', cls.domain.to_json())
        cls.es.indices.refresh(DOMAIN_INDEX_INFO.index)

    @classmethod
    def add_deployment_to_domain(cls):
        deployment = Deployment()
        deployment.city = 'London'
        deployment.countries = ['New Zeland', 'Zambia', 'Vanuatu']
        deployment.region = 'SA'
        deployment.description = 'random description'

        cls.domain.deployment = deployment

    @classmethod
    def make_sms(cls):
        sms_date = datetime(year=2019, month=9, day=12)

        cls.sms_user_recipent = SMS(text='short message sentence',
                      phone_number='+12345678901',
                      date=sms_date,
                      domain=cls.domain_name,
                      couch_recipient=cls.user.user_id,
                      couch_recipient_doc_type='commcareuser')

        cls.sms_case_recipent = SMS(text='short message sentence',
                      phone_number='+12345678901',
                      date=sms_date,
                      domain=cls.domain_name,
                      couch_recipient=cls.case._id,
                      backend_id='super_cool_id',
                      couch_recipient_doc_type='commcarecase')
        
        cls.sms_user_recipent.save()
        cls.sms_case_recipent.save()

    @classmethod
    def make_user(cls):
        user = CommCareUser.create(
            domain=cls.domain_name,
            username='don_mclean',
            password='*****',
            email='simple@email.com'
        )
        user.created_on = datetime(year=2019, month=9, day=12)
        user.save()
        cls.user = user

    @classmethod
    def make_app(cls):
        cls.app = Application(
            domain=cls.domain.name,
            modules=[
                Module(forms=
                       [Form(xmlns='super://legit.xmlns/app')])
            ])

        cls.app.save()

    @classmethod
    def make_xform(cls):
        send_date = datetime(year=2019, month=9, day=12)
        cls.form = XFormInstance(
            domain=cls.domain.name,
            app_id=cls.app._id,
            xmlns='super://legit.xmlns/',
            received_on=send_date,
            server_modified_on=send_date,
            inserted_at=send_date,
            submit_ip="127.0.0.1",
            backend_id='super_cool_id',
            form={"meta": {"userID": cls.user.user_id,
                           "username": cls.user.username}}
        )

        cls.form.save()

    @classmethod
    def make_domain_subscription(cls):
        now = date(year=2019, month=9, day=14)
        then = date(year=2019, month=9, day=10)

        cls.account = BillingAccount.get_or_create_account_by_domain(cls.domain.name, created_by="testing")[0]
        plan = DefaultProductPlan.get_default_plan_version(edition=SoftwarePlanEdition.ADVANCED)

        cls.subscription = Subscription.new_domain_subscription(cls.account, cls.domain.name, plan, then, now)
        cls.subscription.is_active = True
        cls.subscription.save()

    @classmethod
    def send_data_to_elasticsearch(cls):
        ensure_index_deleted(DOMAIN_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, DOMAIN_INDEX_INFO)
        send_to_elasticsearch('domains', cls.domain.to_json())
        cls.es.indices.refresh(DOMAIN_INDEX_INFO.index)

        ensure_index_deleted(USER_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, USER_INDEX_INFO)
        send_to_elasticsearch('users', cls.user.to_json())
        cls.es.indices.refresh(USER_INDEX_INFO.index)

        ensure_index_deleted(SMS_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, SMS_INDEX_INFO)
        send_to_elasticsearch('sms', cls.sms_user_recipent.to_json())
        send_to_elasticsearch('sms', cls.sms_case_recipent.to_json())
        cls.es.indices.refresh(SMS_INDEX_INFO.index)

        ensure_index_deleted(XFORM_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, XFORM_INDEX_INFO)
        send_to_elasticsearch('forms', transform_xform_for_elasticsearch(cls.form.to_json()))
        cls.es.indices.refresh(XFORM_INDEX_INFO.index)

        ensure_index_deleted(CASE_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, CASE_INDEX_INFO)
        send_to_elasticsearch('cases', cls.case.to_json())
        cls.es.indices.refresh(CASE_INDEX_INFO.index)

        ensure_index_deleted(GROUP_INDEX_INFO.index)
        initialize_index_and_mapping(cls.es, GROUP_INDEX_INFO)
        send_to_elasticsearch('groups', cls.group.to_json())
        cls.es.indices.refresh(GROUP_INDEX_INFO.index)

    @classmethod
    def make_case(cls):
        actions = [CommCareCaseAction(
            action_type=CASE_ACTION_CREATE,
            date=datetime(year=2019, month=9, day=11),
        )]

        cls.case = CommCareCase(
            _id='don_mclean',
            domain=cls.domain_name,
            owner_id=cls.user.username,
            user_id=cls.user.user_id,
            type=SUPPLY_POINT_CASE_TYPE,
            opened_on=datetime(year=2019, month=9, day=11),
            opened_by=cls.user.user_id,
            closed_on=datetime(year=2019, month=9, day=14),
            closed_by=cls.user.user_id,
            actions=actions,
        )
        cls.case.save()

    @classmethod
    def add_stockreport(cls):
        cls.stock_report = StockReport(
            form_id=cls.form.form_id,
            date=datetime(year=2019, month=9, day=11),
            type='transfer',
            domain=cls.domain_name,
            server_date=datetime(year=2019, month=9, day=11)
        )
        cls.stock_report.save()

        cls.sql_product = SQLProduct(product_id='product_id', domain=cls.domain.name)

        cls.sql_product.save()

        cls.stock_transaction = StockTransaction(
            report=cls.stock_report,
            section_id=const.SECTION_TYPE_STOCK,
            type=const.TRANSACTION_TYPE_STOCKONHAND,
            case_id=cls.case._id,
            product_id='product_id',
            stock_on_hand=Decimal(10),
        )
        cls.stock_transaction.save()

    @classmethod
    def make_group(cls):
        cls.group = Group(
            domain=cls.domain.name,
            name='wu_tang_clan',
            users=[cls.user.username],
            case_sharing=False,
            reporting=True,
            _id='group_id',
        )
        cls.group.save()

    @classmethod
    def make_sqllocation(cls):
        cls.location_type = LocationType(
            domain=cls.domain_name,
            name="island",
            code="timaeus",
        )
        cls.location_type.save()

        cls.location1 = SQLLocation(
            domain=cls.domain_name,
            location_id="l0cation_id",
            name="Atlantis",
            location_type=cls.location_type,
        )
        cls.location1.save()
        cls.location1.created_at = datetime(year=2019, month=9, day=11)
        cls.location1.save()
