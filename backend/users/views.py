from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from django.shortcuts import get_object_or_404
import logging

from api.pagination import UserPagination
from .serializers import AvatarSerializer, SubscriptionUserSerializer, CustomUserSerializer
from .models import CustomUser, Subscription

logger = logging.getLogger(__name__)

class CustomUserViewSet(DjoserUserViewSet):
    pagination_class = UserPagination

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me'
    )
    def me(self, request, *args, **kwargs):
        try:
            logger.debug(f"User requesting /me/: {request.user}")
            logger.debug(f"Auth header: {request.headers.get('Authorization')}")
            
            if request.user.is_anonymous:
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            serializer = CustomUserSerializer(
                request.user,
                context={'request': request}
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in me view: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer, *args, **kwargs):
        data = serializer.validated_data
        if not data.get('first_name') or not data.get('last_name'):
            raise serializers.ValidationError(
                {'error': 'Поля first_name и last_name являются обязательными'}
            )
        super().perform_create(serializer)

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': 'Это поле обязательное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
            if Subscription.objects.filter(
                user=user, following=following
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if user == following:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            subscription = Subscription.objects.create(
                user=user, following=following)

            serializer = SubscriptionUserSerializer(
                subscription.following, context={'request': request}
            )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(
            user=user, following=following)
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)