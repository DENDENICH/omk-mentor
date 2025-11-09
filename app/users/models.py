from django.db import models
from django.contrib.auth.models import AbstractUser

from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver



ROLE_CHOICES = [
        ("student", "Студент"),
        ("mentor", "Ментор"),
        ("admin", "Админ"),
        ("organizer", "Организатор"),
    ]


class AuthUser(AbstractUser):
    """
    ORM модель для пользователей
    """
    username = models.CharField(max_length=255, unique=True, blank=True, null=True)
    tab_number = models.CharField(
        max_length=255,
        unique=True,
        validators=[RegexValidator(r'^\w+$', 'Табельный номер может содержать только буквы/цифры/нижнее подчеркивание')]
    )



class Profile(models.Model):
    """
    ORM модель для пользователей
    """
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)
    about_me = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField()


    def __repr__(self):
        return f"{self.user.username} ({self.user.email})"

    @receiver(post_save, sender=AuthUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=AuthUser)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()
