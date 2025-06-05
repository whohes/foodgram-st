from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart
)
from users.models import CustomUser, Subscription
from .pagination import Pagination
from .filters import IngredientSearchFilter, RecipeFilter
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    ShortRecipeSerializer,
    CustomUserSerializer,
    SubscriptionUserSerializer,
    AvatarSerializer
)
from .permissions import IsAuthorOrReadOnly


@api_view(['GET'])
def copy_short_link(request, pk):
    recipe = get_object_or_404(Recipe, id=pk)
    return Response({
        'short-link': request.build_absolute_uri(f'/recipes/{recipe.id}/')
    })


class UserProfileViewSet(DjoserUserViewSet):
    pagination_class = Pagination
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all().order_by('id')
    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    def get_permissions(self):
        protected_actions = [
            'me',
            'avatar',
            'subscriptions',
            'subscribe',
        ]
        if self.action in protected_actions:
            return [permissions.IsAuthenticated()]
        if self.action in ['retrieve', 'list']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        url_path='me'
    )
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                data={'avatar': user.avatar.url},
                status=status.HTTP_200_OK
            )
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=False,
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        followed_users = CustomUser.objects.filter(
            followers__user=request.user
        ).order_by('id')
        page = self.paginate_queryset(followed_users)
        serializer = SubscriptionUserSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(CustomUser, id=id)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, following=author
            )
            
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionUserSerializer(
                subscription.following,
                context={'request': request}
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )

        subscription = Subscription.objects.filter(
            user=user, following=author
        ).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого пользователя'},
            status=status.HTTP_400_BAD_REQUEST
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Recipe.objects.all().select_related(
            'author'
        ).prefetch_related(
            'ingredients',
            'ingredient_amounts'
        )
        
        user = self.request.user
        if user.is_authenticated:
            is_favorited = self.request.query_params.get('is_favorited')
            is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
            author = self.request.query_params.get('author')
            
            if is_favorited:
                queryset = queryset.filter(favorites__user=user)
            if is_in_shopping_cart:
                queryset = queryset.filter(in_cart__user=user)
            if author:
                queryset = queryset.filter(author_id=author)
        
        return queryset.order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_relation(self, request, recipe, model, serializer_class):
        obj = model.objects.filter(user=request.user, recipe=recipe).first()
        
        if request.method == "POST":
            if obj:
                return Response(
                    {'error': 'Объект уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = serializer_class(recipe, context={'request': request})
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Объект не найден'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        return self._handle_relation(
            request, recipe, Favorite, ShortRecipeSerializer
        )

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        return self._handle_relation(
            request, recipe, ShoppingCart, ShortRecipeSerializer
        )

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(in_cart__user=request.user)
        ingredients = (
            IngredientInRecipe.objects.filter(recipe__in=recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        if not ingredients:
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_list = []
        for item in ingredients:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            shopping_list.append(f"{name} ({unit}) - {amount}")

        content = "\n".join(shopping_list)
        filename = "shopping_list.txt"
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response 