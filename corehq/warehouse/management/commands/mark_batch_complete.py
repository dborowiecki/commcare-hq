from datetime import datetime

from django.core.management import BaseCommand
from django.core.management import CommandError

from corehq.warehouse.models import Batch


class Command(BaseCommand):
    """
    Example: ./manage.py mark_batch_complete 22
    """
    help = "Usage: ./manage.py mark_batch_complete <batch_id>"

    def add_arguments(self, parser):
        parser.add_argument('batch_id')

    def handle(self, batch_id, **options):
        try:
            batch = Batch.objects.get(pk=batch_id)
        except Batch.DoesNotExist:
            raise CommandError('Invalid batch ID: {}'.format(batch_id))

        if batch.completed_on is None:
            batch.completed_on = datetime.utcnow()
            batch.save()
        else:
            raise CommandError('Batch {} is already marked as complete'.format(batch_id))
