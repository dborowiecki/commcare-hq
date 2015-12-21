from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from corehq.apps.locations.models import SQLLocation
from corehq.apps.users.models import WebUser
from custom.ilsgateway.models import ILSMigrationStats, ILSMigrationProblem
from custom.logistics.mixin import UserMigrationMixin
from custom.logistics.utils import iterate_over_api_objects


class BalanceMigration(UserMigrationMixin):

    def __init__(self, domain, endpoint):
        self.domain = domain
        self.endpoint = endpoint

    def _get_total_counts(self, func, limit=1, **kwargs):
        meta, _ = func(limit=limit, **kwargs)
        return meta['total_count'] if meta else 0

    @transaction.atomic
    def validate_web_users(self, date=None):
        unique_usernames = set()
        for web_user in iterate_over_api_objects(
            self.endpoint.get_webusers, filters=dict(date_updated__gte=date)
        ):
            if web_user.email:
                username = web_user.email.lower()
            else:
                username = web_user.username.lower()
                try:
                    validate_email(username)
                except ValidationError:
                    # We are not migrating users without valid email in v1
                    continue

            unique_usernames.add(username)
            couch_web_user = WebUser.get_by_username(username)
            if not couch_web_user or self.domain not in couch_web_user.get_domains():
                description = "Not exists"
                ILSMigrationProblem.objects.get_or_create(
                    domain=self.domain,
                    object_type='webuser',
                    description=description,
                    external_id=web_user.email or web_user.username
                )
                continue

            if not web_user.location:
                continue

            try:
                sql_location = SQLLocation.objects.get(external_id=web_user.location, domain=self.domain)
                if couch_web_user.get_domain_membership(self.domain).location_id != sql_location.location_id:
                    ILSMigrationProblem.objects.get_or_create(
                        domain=self.domain,
                        object_type='webuser',
                        description='Location not assigned',
                        external_id=web_user.email or web_user.username
                    )
                else:
                    ILSMigrationProblem.objects.filter(
                        domain=self.domain,
                        external_id=web_user.email or web_user.username
                    ).delete()
            except SQLLocation.DoesNotExist:
                # Location is inactive in v1 or it's an error in location migration
                continue
        migration_stats = ILSMigrationStats.objects.get(domain=self.domain)
        migration_stats.web_users_count = len(unique_usernames)
        migration_stats.save()

    def balance_migration(self, date=None):
        products_count = self._get_total_counts(self.endpoint.get_products)
        locations_count = self._get_total_counts(
            self.endpoint.get_locations,
            filters=dict(is_active=True)
        )
        sms_users_count = self._get_total_counts(self.endpoint.get_smsusers)

        stats, _ = ILSMigrationStats.objects.get_or_create(domain=self.domain)
        stats.products_count = products_count
        stats.locations_count = locations_count
        stats.sms_users_count = sms_users_count
        stats.save()

        self.validate_web_users(date)
