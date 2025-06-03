from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.serializers import CustomUserSerializer
from .models import (Favorite, Ingredient, IngredientInRecipe,
                     Recipe, ShoppingCart)


class IngredientAmountValidator:
    def __call__(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше нуля'
            )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('id',)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(validators=[IngredientAmountValidator()])

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'name', 'image', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один ингредиент'
            )
        
        seen_ingredients = set()
        for item in value:
            ingredient = item['ingredient']
            if ingredient.id in seen_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными'
                )
            seen_ingredients.add(ingredient.id)
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredient_data = validated_data.pop('ingredient_amounts')
        recipe = Recipe.objects.create(**validated_data)
        self._set_ingredients(recipe, ingredient_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredient_data = validated_data.pop('ingredient_amounts', None)
        super().update(instance, validated_data)
        
        if ingredient_data is not None:
            instance.ingredient_amounts.all().delete()
            self._set_ingredients(instance, ingredient_data)
        return instance

    def _set_ingredients(self, recipe, ingredient_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredient_data
        ])

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'У рецепта должна быть картинка'}
            )
        return data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id', 'author', 'is_favorited',
                            'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_cart.filter(user=request.user).exists()