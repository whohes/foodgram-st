from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from users.models import CustomUser
from .const import (
    INGREDIENT_NAME_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    UNIT_MAX_LENGTH,
    MIN_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
)


class Ingredient(models.Model):
    name = models.CharField(
        "Название", max_length=INGREDIENT_NAME_MAX_LENGTH, unique=True
    )
    measurement_unit = models.CharField("Единица измерения", max_length=UNIT_MAX_LENGTH)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_measurement"
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="recipes"
    )
    name = models.CharField("Название", max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField("Фото", upload_to="recipes/")
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления", validators=[MinValueValidator(MIN_COOKING_TIME)]
    )
    ingredients = models.ManyToManyField(Ingredient, through="IngredientInRecipe")
    pub_date = models.DateTimeField("Дата публикации", default=timezone.now)

    class Meta:
        ordering = ["name"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredient_amounts"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        "Колчиество", validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} ({self.amount} {self.ingredient.measurement_unit})"


class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorites"
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_user_recipe_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="in_cart")

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique user recipe shopping_cart"
            )
        ]