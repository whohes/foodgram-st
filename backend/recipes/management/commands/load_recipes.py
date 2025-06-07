import json 
import os 
from django.core.management.base import BaseCommand 
from django.core.files import File 
from recipes.models import Recipe, Ingredient, IngredientInRecipe 
from users.models import User 
 
 
class Command(BaseCommand): 
    help = 'Load recipes from data/recipes.json' 
 
    def handle(self, *args, **kwargs): 
        try: 
            with open('data/recipes.json', 'r', encoding='utf-8') as file: 
                data = json.load(file) 
                for item in data: 
                    try: 
                        author = User.objects.get(username=item['author']) 
                        self.stdout.write(f"\nProcessing recipe: {item['name']}")
                         
                        recipe = Recipe.objects.filter( 
                            name=item['name'], 
                            author=author 
                        ).first() 
 
                        if recipe: 
                            recipe.text = item['text'] 
                            recipe.cooking_time = item['cooking_time'] 
                            recipe.save() 
                             
                            recipe.ingredient_amounts.all().delete() 
                            action = "Updated" 
                        else: 
                            recipe = Recipe.objects.create( 
                                name=item['name'], 
                                text=item['text'], 
                                cooking_time=item['cooking_time'], 
                                author=author 
                            ) 
                            action = "Created" 
 
                        # Обрабатываем изображение 
                        # Используем путь к изображению как есть, относительно data/
                        image_path = os.path.join('data', item['image'])
                        self.stdout.write(f"Looking for image at: {image_path}")
                        if os.path.exists(image_path): 
                            self.stdout.write(f"Found image file: {image_path}")
                            with open(image_path, 'rb') as img_file: 
                                # Сохраняем только имя файла, без пути photos/
                                image_name = os.path.basename(item['image'])
                                recipe.image.save( 
                                    image_name, 
                                    File(img_file), 
                                    save=True 
                                ) 
                                self.stdout.write(f"Saved image as {image_name}")
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Image file not found: {image_path}"
                                )
                            )
 
                        # Добавляем ингредиенты 
                        self.stdout.write("\nProcessing ingredients:")
                        for ingredient_item in item['ingredients']: 
                            ingredient_name = ingredient_item['name'].strip()
                            self.stdout.write(f"\nLooking for ingredient: {ingredient_name}")
                            try:
                                # Сначала пробуем точное совпадение
                                ingredient = Ingredient.objects.get(name=ingredient_name)
                                self.stdout.write(f"Found ingredient in DB: {ingredient.name} (id: {ingredient.id})")
                                
                                # Проверяем, не был ли уже добавлен этот ингредиент
                                existing = IngredientInRecipe.objects.filter(
                                    recipe=recipe,
                                    ingredient=ingredient
                                ).first()
                                
                                if existing:
                                    self.stdout.write(f"Ingredient already added to recipe: {ingredient.name}")
                                else:
                                    IngredientInRecipe.objects.create( 
                                        recipe=recipe, 
                                        ingredient=ingredient, 
                                        amount=ingredient_item['amount'] 
                                    ) 
                                    self.stdout.write(f"Added ingredient to recipe: {ingredient.name} ({ingredient_item['amount']})")
                            except Ingredient.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'Ingredient not found: {ingredient_name}'
                                    )
                                )
                                # Показываем похожие ингредиенты
                                similar = Ingredient.objects.filter(name__icontains=ingredient_name.split()[0])
                                if similar:
                                    self.stdout.write("Similar ingredients found:")
                                    for s in similar:
                                        self.stdout.write(f"- {s.name}")
                                # Удаляем рецепт, если не нашли ингредиент
                                recipe.delete()
                                raise Exception(f'Required ingredient not found: {ingredient_name}')
 
                        self.stdout.write( 
                            self.style.SUCCESS( 
                                f'{action} recipe {recipe.name}' 
                            ) 
                        ) 
                    except User.DoesNotExist: 
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
