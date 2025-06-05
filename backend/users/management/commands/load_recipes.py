import json
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from recipes.models import Recipe, Ingredient, IngredientInRecipe
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Load recipes from data/recipes.json'

    def handle(self, *args, **kwargs):
        try:
            with open('data/recipes.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    try:
                        # Получаем автора рецепта
                        author = CustomUser.objects.get(username=item['author'])
                        
                        # Пытаемся найти существующий рецепт
                        recipe = Recipe.objects.filter(
                            name=item['name'],
                            author=author
                        ).first()

                        if recipe:
                            # Обновляем существующий рецепт
                            recipe.text = item['text']
                            recipe.cooking_time = item['cooking_time']
                            recipe.save()
                            
                            # Обновляем ингредиенты
                            recipe.ingredient_amounts.all().delete()
                        else:
                            # Создаем новый рецепт
                            recipe = Recipe.objects.create(
                                name=item['name'],
                                text=item['text'],
                                cooking_time=item['cooking_time'],
                                author=author
                            )

                        # Обрабатываем изображение
                        image_path = os.path.join('data', item['image'])
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as img_file:
                                recipe.image.save(
                                    os.path.basename(item['image']),
                                    File(img_file),
                                    save=True
                                )

                        # Добавляем ингредиенты
                        for ingredient_item in item['ingredients']:
                            ingredient, created = Ingredient.objects.get_or_create(
                                name=ingredient_item['name'],
                                defaults={'measurement_unit': 'г'}
                            )
                            IngredientInRecipe.objects.create(
                                recipe=recipe,
                                ingredient=ingredient,
                                amount=ingredient_item['amount']
                            )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully {"updated" if not recipe else "created"} recipe {recipe.name}'
                            )
                        )
                    except CustomUser.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Author {item["author"]} not found'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to process recipe {item["name"]}: {e}'
                            )
                        )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'File data/recipes.json not found'
                )
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(
                    'Invalid JSON in data/recipes.json'
                )
            ) 