from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import logging

from .serializers import AvatarSerializer, SubscriptionUserSerializer, CustomUserSerializer
from .models import CustomUser, Subscription

logger = logging.getLogger(__name__)


class UserPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(DjoserUserViewSet):
    pagination_class = UserPagination

    def get_permissions(self):
        if self.action in ['retrieve', 'list', 'me']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me'
    )
    def me(self, request, *args, **kwargs):
        serializer = CustomUserSerializer(
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
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        followed_users = CustomUser.objects.filter(
            followers__user=user
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(followed_users, request=request)
        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        following = get_object_or_404(CustomUser, id=id)

        if request.method == 'POST':
            if user == following:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, following=following
            )
            
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionUserSerializer(
                subscription.following, context={'request': request}
            )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(
            user=user, following=following
        ).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого пользователя'},
            status=status.HTTP_400_BAD_REQUEST
        )