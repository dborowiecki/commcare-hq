from django.core.management.base import LabelCommand
from corehq.apps.domain.models import Domain, DocDomainMapping


class Command(LabelCommand):
    help = """
    Move domain's document id, name and last_modified to sql table.
    """

    def handle(self, *args, **options):
        print 'Moving data started'
        mappings = [
            DocDomainMapping(
                document_id=domain.get_id,
                name=domain.name,
                last_modified=domain.last_modified
            )
            for domain in Domain.get_all()
        ]
        DocDomainMapping.objects.bulk_create(mappings)
        print 'Moving data finished successfully'
