import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из recipes/ingredients.json'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.json', encoding='utf-8') as file:
            data = json.load(file)
            created_count = 0
            skipped_count = 0
            
            for item in data:
                _, created = Ingredient.objects.get_or_create(
                    name=item['name'],
                    defaults={'measurement_unit': item['measurement_unit']}
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {created_count} ingredients. '
                    f'Skipped {skipped_count} existing ingredients.'
                )
            )