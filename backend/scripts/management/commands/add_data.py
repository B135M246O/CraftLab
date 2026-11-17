import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tags_ingr.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить материалы из CSV: название,единица измерения.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Путь к CSV без заголовка')
        parser.add_argument('tab_name', nargs='?', choices=['tags_ingr_ingredient'])

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open(options['path'], encoding='utf-8-sig', newline='') as source:
                for number, row in enumerate(csv.reader(source), start=1):
                    if len(row) != 2 or not all(part.strip() for part in row):
                        raise CommandError(f'Неверная строка CSV: {number}')
                    Ingredient.objects.get_or_create(
                        name=row[0].strip(), measurement_unit=row[1].strip())
        except OSError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS('Материалы загружены.'))
