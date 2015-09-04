from datetime import datetime
import logging
from tastypie.paginator import Paginator
from corehq import Domain
from corehq.apps.accounting.models import Subscription
from corehq.apps.api.resources import HqBaseResource
from corehq.apps.api.resources.v0_1 import (
    CustomResourceMeta,
    AdminAuthentication,
)
from corehq.apps.domain.models import DocDomainMapping
from corehq.apps.es.domains import DomainES

from tastypie import fields
from tastypie.exceptions import NotFound
import operator
from dimagi.utils.couch.database import iter_docs


def _get_domain(bundle):
    return bundle.obj


def get_truth(inp, relate, cut):
    ops = {'gt': operator.gt,
           'lt': operator.lt,
           'gte': operator.ge,
           'lte': operator.le}
    if relate not in ops:
        return True
    else:
        cut_datetime = datetime.strptime(cut, '%Y-%m-%d')
        return ops[relate](inp, cut_datetime)


class CustomPaginator(Paginator):

    def get_slice(self, limit, offset):
        return self.objects

    def get_count(self):
        return DocDomainMapping.objects.count()


class DomainMetadataResource(HqBaseResource):
    billing_properties = fields.DictField()
    calculated_properties = fields.DictField()
    domain_properties = fields.DictField()

    def dehydrate_billing_properties(self, bundle):
        domain = _get_domain(bundle)
        plan_version, subscription = (
            Subscription.get_subscribed_plan_by_domain(domain)
        )
        return {
            "date_start": (subscription.date_start
                           if subscription is not None else None),
            "date_end": (subscription.date_end
                         if subscription is not None else None),
            "plan_version": plan_version,
        }

    def dehydrate_calculated_properties(self, bundle):
        domain = _get_domain(bundle)
        try:
            es_data = (DomainES()
                       .in_domains([domain.name])
                       .run()
                       .raw_hits[0]['_source'])
            return {
                raw_hit: es_data[raw_hit]
                for raw_hit in es_data if raw_hit[:3] == 'cp_'
            }
        except IndexError:
            logging.exception('Problem getting calculated properties for {}'.format(domain.name))
            return {}

    def dehydrate_domain_properties(self, bundle):
        return _get_domain(bundle)._doc

    def obj_get(self, bundle, **kwargs):
        domain = Domain.get_by_name(kwargs.get('domain'))
        if domain is None:
            raise NotFound
        return domain

    def obj_get_list(self, bundle, **kwargs):
        if kwargs.get('domain'):
            return [self.obj_get(bundle, **kwargs)]
        else:
            filters = {}
            if hasattr(bundle.request, 'GET'):
                filters = bundle.request.GET

            limit = int(filters.get('limit', 10))
            offset = int(filters.get('offset', 0))
            params = {}
            if 'last_modified__lte' in filters:
                params['last_modified__lte'] = filters['last_modified__lte']

            if 'last_modified__gte' in filters:
                params['last_modified__gte'] = filters['last_modified__gte']

            mappings = DocDomainMapping.objects.filter(**params).order_by('last_modified')
            return map(
                Domain.wrap,
                iter_docs(Domain.get_db(), mappings.values_list('document_id', flat=True)[offset:offset + limit])
            )

    class Meta(CustomResourceMeta):
        authentication = AdminAuthentication()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        object_class = Domain
        resource_name = 'project_space_metadata'
        paginator_class = CustomPaginator
