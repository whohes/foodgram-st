from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from .const import USERNAME_MAX_LENGTH


class CustomUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        default=None,
        null=True
    )
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=(r"^[\w.@+-]+$"),
                message=(
                    "Имя пользователя может содержать только буквы, "
                    "цифры и знаки @/./+/-/_"
                ),
                code="invalid_username",
            )
        ],
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    following = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return f"{self.user.username} подписан на {self.following.username}"
