from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum

from urlshortner.utils import shorten_url

from .filters import IngredientSearchFilter, RecipeFilter
from .serializers import IngredientSerializer, RecipeSerializer
from .models import Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart
from api.permissions import IsAuthorOrReadOnly
from api.pagination import UserPagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = UserPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_delete_recipe(self, request, user, recipe, model):
        obj = model.objects.filter(user=user, recipe=recipe).first()
        if request.method == "POST":
            if obj:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            return Response(
                data={
                    "id": recipe.id,
                    "name": recipe.name,
                    "image": recipe.image.url,
                    "cooking_time": recipe.cooking_time,
                },
                status=status.HTTP_201_CREATED,
            )

        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_delete_recipe(request, user, recipe, Favorite)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        return self.add_delete_recipe(request, user, recipe, ShoppingCart)

    @action(methods=["get"], detail=True, url_path="get-link")
    def get_short_link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        default_link = request.build_absolute_uri(f"/api/recipes/{pk}/")
        short_link = shorten_url(url=default_link, is_permanent=False)
        return Response(data={"short-link": short_link})

    @action(
        methods=["get"],
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(in_cart__user=request.user)

        ingredients = (
            IngredientInRecipe.objects.filter(recipe__in=recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        shopping_list = []
        for item in ingredients:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            shopping_list.append(f"{name} ({unit}) - {amount}")

        if not shopping_list:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        content = "\n".join(shopping_list)
        filename = "shopping_list.txt"
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response