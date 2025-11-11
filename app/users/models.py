from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser

from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


def product_preview_directory_path(instance: "Profile", filename: str) -> str:
    return "profiles/profile_{pk}/avatar/{filename}".format(
        pk=instance.pk,
        filename=filename
    )


class AuthUser(AbstractUser):
    """
    ORM модель для пользователей
    """
    username = models.CharField(max_length=255, unique=True, null=True)
    tab_number = models.CharField(
        max_length=255,
        unique=True,
        validators=[RegexValidator(r'^\w+$', 'Tab number must be words/digits/underscore')]
    )
    is_auth = models.BooleanField(default=False)

    USERNAME_FIELD = 'tab_number'
    REQUIRED_FIELDS = ['username', 'email']

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.tab_number}"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.tab_number}"


class Profile(models.Model):
    """
    ORM модель для пользователей
    """
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)
    account_role = models.CharField(
        max_length=20,
        choices=(
            ('admin', 'Администратор'),
            ('organizer', 'Организатор'),
        ),
        null=True, blank=True
    )
    avatar = models.ImageField(null=True, blank=True, upload_to=product_preview_directory_path)


    def __repr__(self):
        return f"{self.user.username} ({self.user.email})"
    
    def __str__(self):
        return f"{self.user.username} ({self.user.email})"

    @receiver(post_save, sender=AuthUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=AuthUser)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

