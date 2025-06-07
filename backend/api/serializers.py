from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.validators import UniqueTogetherValidator
from django.shortcuts import get_object_or_404

from recipes.models import (Ingredient, IngredientInRecipe, Recipe)
from api.constants import MIN_AMOUNT, AMOUNT_ERROR
from users.models import User, Subscription


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class UserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'password', 'avatar'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.followers.filter(user=request.user).exists()


class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionUserSerializer(
            instance.author, context={'request': request}
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('id',)


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'name', 'image', 'text', 
            'cooking_time', 'author', 'is_favorited', 
            'is_in_shopping_cart'
        )

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

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один ингредиент'
            )
        
        seen_ingredients = set()
        for item in value:
            ingredient = item['ingredient']
            amount = item['amount']

            if amount < MIN_AMOUNT:
                raise serializers.ValidationError(
                    f'Количество ингредиента {ingredient.name} должно быть больше нуля'
                )

            if ingredient.id in seen_ingredients:
                raise serializers.ValidationError(
                    f'Ингредиент {ingredient.name} уже добавлен в рецепт'
                )
            seen_ingredients.add(ingredient.id)
        return value

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'У рецепта должна быть картинка'}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance.ingredient_amounts.all().delete()
        self._set_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _set_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeReadSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=True)
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