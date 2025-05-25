from django.contrib import admin
from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name", "date_joined")

    # Поиск по юзернейму и почте
    search_fields = ("username", "email")


admin.site.register(CustomUser, CustomUserAdmin)