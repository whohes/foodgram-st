import json

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from users.models import User


class Command(BaseCommand):
    help = 'Load users from data/users.json'

    def handle(self, *args, **kwargs):
        try:
            with open('data/users.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            for item in data:
                    try:
                        if not User.objects.filter(
                            username=item['username']
                        ).exists():
                            user = User.objects.create(
                                email=item['email'],
                                username=item['username'],
                                first_name=item['first_name'],
                                last_name=item['last_name'],
                                password=make_password(item['password'])
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Successfully created user {user.username}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'User {item["username"]} already exists'
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to create user {item["username"]}: {e}'
                            )
                        )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    'File data/users.json not found'
                )
            ) 