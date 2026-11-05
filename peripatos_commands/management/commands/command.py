import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Addind inittial data"

    def handle(self, *args, **options):
        # Define command logic here
        pass
