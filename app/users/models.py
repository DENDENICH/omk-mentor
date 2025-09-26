from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    """
    ORM модель для ролей
    """

    ROLE_CHOICES = [
        ("student", "Студент"),
        ("mentor", "Ментор"),
        ("admin", "Админ"),
        ("organizer", "Организатор"),
    ]

    role = models.CharField(max_length=255, choices=ROLE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")

    def __str__(self):
        return f"{self.role} - {self.user.username}"
